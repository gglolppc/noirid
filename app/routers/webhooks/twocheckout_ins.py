from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response
from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from app.repos.payments import PaymentRepo
from app.services.payment_state import apply_payment_status
from app.services.twocheckout import TwoCOConfig, TwoCOService
from app.services.twocheckout_ins_parser import map_to_internal_status, pick


import logging
from typing import Any

log = logging.getLogger("2co.ipn")


SENSITIVE_KEYS = {
    "card", "cc", "cvv", "cvc", "security", "pass", "password", "secret", "key",
    "signature", "hash", "authorization", "token",
}


def _sanitize(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for k, v in payload.items():
        lk = k.lower()
        if any(s in lk for s in SENSITIVE_KEYS):
            safe[k] = "***"
        else:
            # чтобы логи не раздувались
            s = str(v)
            safe[k] = (s[:300] + "…") if len(s) > 300 else s
    return safe


router = APIRouter(prefix="/webhooks/2co", tags=["webhooks"])


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
async def ipn_probe():
    # 2Checkout часто делает GET/HEAD, чтобы проверить доступность URL
    return Response(content="OK", media_type="text/plain")

@router.head("/ipn", include_in_schema=False)
async def ipn_probe_head():
    return Response(status_code=200)

@router.post("/ipn", include_in_schema=False)
async def ins_listener(request: Request, session: AsyncSession = Depends(get_async_session)):
    # IPN прилетает как Form Data
    form = await request.form()

    items = list(form.multi_items())  # сохраняет порядок и дубли

    client = getattr(request, "client", None)
    client_host = getattr(client, "host", None)
    ct = request.headers.get("content-type")
    ua = request.headers.get("user-agent")

    log.info(
        "2CO IPN received",
        extra={
            "client_ip": client_host,
            "content_type": ct,
            "user_agent": ua,
            "keys": sorted(set([k for k, _ in items])),
            "payload_preview": _sanitize(dict(items)),
        },
    )
    payload = dict(items)
    cfg = _cfg()

    # 1. Проверка подписи (используем новый метод для IPN)
    is_valid = TwoCOService.verify_ipn_hash_items(cfg.secret_key, items)
    log.info(
        "2CO IPN signature checked",
        extra={
            "is_valid": is_valid,
            "merchant_order_id": payload.get("REFNOEXT"),
            "provider_refno": payload.get("REFNO") or payload.get("ORDERNO"),
        },
    )

    if not is_valid:
        # ВАЖНО: лучше 200, чтобы не словить ретраи/шторм, но при этом лог у тебя останется
        return Response(status_code=200, content="OK", media_type="text/plain")

    # связь с нашим order:
    merchant_order_id = payload.get("REFNOEXT")
    # provider order number:
    provider_order_number = pick(payload, "REFNO", "ORDERNO", "sale_id")
    invoice_id = pick(payload, "invoice_id", "INVOICE_ID")

    internal_status, extracted = map_to_internal_status(payload)
    log.info(
        "2CO IPN parsed",
        extra={
            "merchant_order_id": merchant_order_id,
            "provider_order_number": provider_order_number,
            "invoice_id": invoice_id,
            "internal_status": internal_status,
            "extracted": extracted,
        },
    )

    # 1) Обновляем Order (если нашли)
    if merchant_order_id:
        order = await CheckoutRepo.get_order_any(session, str(merchant_order_id))
        if order:
            if internal_status:
                order.payment_status = apply_payment_status(order.payment_status, internal_status)

                # если реально paid — можно двигать бизнес-статус
                if order.payment_status == "paid" and order.status == "pending_payment":
                    order.status = "paid"
                if order.payment_status == "refunded" and order.status != "refunded":
                    order.status = "refunded"
                if order.payment_status == "canceled" and order.status != "canceled":
                    order.status = "canceled"

    # 2) Обновляем Payment (если найдём)
    payment = None
    if provider_order_number:
        payment = await PaymentRepo.get_by_provider_order(session, "2checkout", str(provider_order_number))
    if not payment and merchant_order_id:
        payment = await PaymentRepo.get_latest_for_order(session, str(merchant_order_id))
    if payment:
        if internal_status:
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
    response_content = TwoCOService.calculate_ipn_response(cfg.secret_key, payload)
    return Response(content=response_content, media_type="text/html")
