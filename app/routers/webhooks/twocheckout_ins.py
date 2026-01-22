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


@router.post("/ipn", include_in_schema=False)
async def ins_listener(request: Request, session: AsyncSession = Depends(get_async_session)):
    # IPN прилетает как Form Data
    form = await request.form()
    items = list(form.multi_items())  # сохраняет порядок и дубли
    payload = dict(items)
    cfg = _cfg()

    # 1. Проверка подписи (используем новый метод для IPN)
    if not TwoCOService.verify_ipn_hash(cfg.secret_key, payload):
        raise HTTPException(status_code=400, detail="Invalid IPN signature")

    # связь с нашим order:
    merchant_order_id = payload.get("REFNOEXT")
    # provider order number:
    provider_order_number = pick(payload, "REFNO", "ORDERNO", "sale_id")
    invoice_id = pick(payload, "invoice_id", "INVOICE_ID")

    internal_status, extracted = map_to_internal_status(payload)

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
