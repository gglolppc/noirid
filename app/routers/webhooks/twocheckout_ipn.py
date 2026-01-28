from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.core.directories import STATIC_DIR
from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from app.repos.orders import OrdersRepo
from app.repos.payments import PaymentRepo
from app.services.order_previews import persist_order_previews
from app.services.payment_state import apply_payment_status
from app.services.twocheckout import TwoCOConfig, TwoCOService
from app.services.twocheckout_ins_parser import map_to_internal_status, pick

log = logging.getLogger("2co.ipn")

router = APIRouter(prefix="/webhooks/2co", tags=["webhooks"])

# ---- security/logging helpers ----

SENSITIVE_KEYS = {
    "card",
    "cc",
    "cvv",
    "cvc",
    "security",
    "pass",
    "password",
    "secret",
    "key",
    "signature",
    "hash",
    "authorization",
    "token",
}

AMOUNT_TOLERANCE = Decimal("0.10")  # +/- $1


def _sanitize(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for k, v in payload.items():
        lk = k.lower()
        if any(s in lk for s in SENSITIVE_KEYS):
            safe[k] = "***"
        else:
            s = str(v)
            safe[k] = (s[:300] + "…") if len(s) > 300 else s
    return safe


def _to_decimal(val: Any) -> Decimal | None:
    try:
        if val is None:
            return None
        return Decimal(str(val))
    except (InvalidOperation, TypeError):
        return None


def _amount_matches(expected: Decimal, received: Decimal) -> bool:
    return abs(expected - received) <= AMOUNT_TOLERANCE


def _cfg() -> TwoCOConfig:
    merchant_code = os.getenv("TCO_MERCHANT_CODE", "")
    secret_word = os.getenv("TCO_SECRET_WORD", "")
    secret_key = os.getenv("TCO_SECRET_KEY", "")
    demo = os.getenv("TCO_DEMO", "1") == "1"
    if not merchant_code or not secret_word or not secret_key:
        raise RuntimeError("2CO secrets not set")
    return TwoCOConfig(
        merchant_code=merchant_code,
        secret_word=secret_word,
        secret_key=secret_key,
        demo=demo,
        return_url="",
    )


@router.get("/ipn", include_in_schema=False)
async def ipn_probe() -> Response:
    # 2Checkout часто делает GET/HEAD, чтобы проверить доступность URL
    return Response(content="OK", media_type="text/plain")


@router.head("/ipn", include_in_schema=False)
async def ipn_probe_head() -> Response:
    return Response(status_code=200)


@router.post("/ipn", include_in_schema=False)
async def ipn_listener(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    form = await request.form()
    items = list(form.multi_items())  # сохраняет порядок и дубли
    payload: dict[str, Any] = dict(items)

    client = getattr(request, "client", None)
    client_host = getattr(client, "host", None)

    cfg = _cfg()

    # 1) Подпись
    is_valid = TwoCOService.verify_ipn_signature_sha2_256(cfg.secret_key, items)

    log.info(
        "2CO IPN received: %s",
        {
            "client_ip": client_host,
            "refnoext": payload.get("REFNOEXT"),
            "orderno": payload.get("ORDERNO") or payload.get("REFNO"),
            "orderstatus": payload.get("ORDERSTATUS"),
            "is_valid": is_valid,
        },
    )
    log.debug(
        "2CO IPN debug: %s",
        {
            "content_type": request.headers.get("content-type"),
            "user_agent": request.headers.get("user-agent"),
            "keys": sorted({k for k, _ in items}),
            "payload_preview": _sanitize(dict(items)),
        },
    )

    # Невалидная подпись — не применяем, но отвечаем 200, чтобы не ловить ретраи
    if not is_valid:
        return Response(status_code=200, content="OK", media_type="text/plain")

    # 2) Идентификаторы
    merchant_order_id = (payload.get("REFNOEXT") or "").strip() or None  # твой order_number (NRD-...)
    provider_order_number = pick(payload, "REFNO", "ORDERNO", "sale_id")
    invoice_id = pick(payload, "invoice_id", "INVOICE_ID")

    # 3) Статус
    internal_status, extracted = map_to_internal_status(payload)

    log.info(
        "2CO IPN processed: %s",
        {
            "merchant_order_id": merchant_order_id,
            "provider_order_number": provider_order_number,
            "invoice_id": invoice_id,
            "internal_status": internal_status,
            "order_status": extracted.get("order_status"),
            "invoice_status": extracted.get("invoice_status"),
            "fraud_status": extracted.get("fraud_status"),
        },
    )

    # 4) Ищем Order
    order = None
    if merchant_order_id:
        order = await OrdersRepo.get_by_order_number(session, merchant_order_id)
        if not order:
            # Если REFNOEXT не совпал — дальше гадать опасно: можем заапдейтить чужой payment.
            log.error("Order not found for REFNOEXT: %s", merchant_order_id)
            response_content = TwoCOService.calculate_ipn_response(cfg.secret_key, payload)
            return Response(content=response_content, media_type="text/plain")

    # 5) Ищем Payment
    payment = None
    if provider_order_number:
        payment = await PaymentRepo.get_by_provider_order(session, "2checkout", str(provider_order_number))

    if payment is None and order is not None:
        payment = await PaymentRepo.get_latest_for_order(session, str(order.id))

    # 6) Сумма/валюта (для paid — строгий гейт по сумме, валюта только если есть expected_currency)
    received_amount = _to_decimal(payload.get("IPN_TOTALGENERAL"))
    received_currency = (payload.get("CURRENCY") or "").upper().strip() or None

    expected_amount: Decimal | None = None
    expected_currency: str | None = None

    if payment is not None:
        expected_amount = getattr(payment, "amount", None)
        expected_currency = (getattr(payment, "currency", None) or "").upper().strip() or None

    if expected_amount is None and order is not None:
        expected_amount = getattr(order, "total", None)

    if expected_currency is None and order is not None:
        expected_currency = (getattr(order, "currency", None) or "").upper().strip() or None

    amount_ok = True
    currency_ok = True

    if expected_amount is not None and received_amount is not None:
        amount_ok = _amount_matches(expected_amount, received_amount)
        if not amount_ok:
            log.error(
                "2CO amount mismatch: %s",
                {
                    "merchant_order_id": merchant_order_id,
                    "provider_order_number": provider_order_number,
                    "expected_amount": str(expected_amount),
                    "received_amount": str(received_amount),
                    "tolerance": str(AMOUNT_TOLERANCE),
                },
            )
    else:
        log.warning(
            "2CO amount check skipped (missing expected/received): %s",
            {
                "merchant_order_id": merchant_order_id,
                "provider_order_number": provider_order_number,
                "expected_amount": str(expected_amount) if expected_amount is not None else None,
                "received_amount": str(received_amount) if received_amount is not None else None,
            },
        )

    if expected_currency and received_currency:
        currency_ok = (expected_currency == received_currency)
        if not currency_ok:
            log.error(
                "2CO currency mismatch: %s",
                {
                    "merchant_order_id": merchant_order_id,
                    "provider_order_number": provider_order_number,
                    "expected_currency": expected_currency,
                    "received_currency": received_currency,
                },
            )
    else:
        # валюта может отсутствовать у тебя в базе — не блокируем paid только из-за этого
        log.debug(
            "2CO currency check skipped: %s",
            {
                "merchant_order_id": merchant_order_id,
                "provider_order_number": provider_order_number,
                "expected_currency": expected_currency,
                "received_currency": received_currency,
            },
        )

    def _can_apply_status(status: str | None) -> bool:
        if not status:
            return False

        if status == "paid":
            # paid применяем ТОЛЬКО если можем подтвердить сумму
            if expected_amount is None or received_amount is None or not amount_ok:
                return False

            # валюту проверяем только если она у нас есть (expected_currency)
            if expected_currency and received_currency and not currency_ok:
                return False

        return True

    # 7) Обновляем Order
    if order is not None and internal_status:
        if not _can_apply_status(internal_status):
            if internal_status == "paid":
                log.error(
                    "2CO paid ignored due to verification failure: %s",
                    {
                        "merchant_order_id": merchant_order_id,
                        "provider_order_number": provider_order_number,
                        "expected_amount": str(expected_amount) if expected_amount is not None else None,
                        "received_amount": str(received_amount) if received_amount is not None else None,
                        "expected_currency": expected_currency,
                        "received_currency": received_currency,
                    },
                )
        else:
            order.payment_status = apply_payment_status(order.payment_status, internal_status)

            if order.payment_status == "paid" and order.status == "pending_payment":
                order.status = "paid"

                if not getattr(order, "items", None):
                    log.error("Paid order has no items loaded: %s (%s)", order.id, order.order_number)
                else:
                    persist_order_previews(
                        order=order,
                        static_dir=Path(STATIC_DIR),
                        session=session,
                    )

            if order.payment_status == "refunded" and order.status != "refunded":
                order.status = "refunded"

            if order.payment_status == "canceled" and order.status != "canceled":
                order.status = "canceled"

    # 8) Обновляем Payment
    if payment is not None:
        if internal_status and _can_apply_status(internal_status):
            payment.status = internal_status

        if provider_order_number:
            payment.provider_order_number = str(provider_order_number)

        payment.provider_invoice_id = str(invoice_id) if invoice_id else payment.provider_invoice_id
        payment.provider_message_type = extracted.get("message_type")
        payment.provider_order_status = extracted.get("order_status")
        payment.provider_invoice_status = extracted.get("invoice_status")
        payment.provider_approve_status = extracted.get("approve_status")

        payment.raw_payload = payload

    await session.commit()

    # 9) Ответ 2CO
    response_content = TwoCOService.calculate_ipn_response(cfg.secret_key, payload)
    return Response(content=response_content, media_type="text/plain")
