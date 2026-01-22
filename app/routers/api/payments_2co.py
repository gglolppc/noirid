from __future__ import annotations

import os
from decimal import Decimal

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import Payment
from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from app.repos.payments import PaymentRepo
from app.services.cart import CartService
from app.services.twocheckout import TwoCOConfig, TwoCOService

router = APIRouter(prefix="/api/payments/2co", tags=["payments"])

SESSION_ORDER_KEY = "order_id"
load_dotenv()

def _two_co_cfg(request: Request) -> TwoCOConfig:
    merchant_code = os.getenv("TCO_MERCHANT_CODE", "")
    secret_word = os.getenv("TCO_SECRET_WORD", "")
    secret_key = os.getenv("TCO_SECRET_KEY", "")
    demo = os.getenv("TCO_DEMO", "1") == "1"
    base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    if not merchant_code or not secret_word or not secret_key:
        raise RuntimeError("TCO_MERCHANT_CODE / TCO_SECRET_WORD / TCO_SECRET_KEY are not set")

    return TwoCOConfig(
        merchant_code=merchant_code,
        secret_word=secret_word,
        secret_key=secret_key,
        demo=demo,
        return_url=f"{base_url}/payment/2co/return",
    )


@router.post("/start")
async def start_2co_payment(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order_id = request.session.get(SESSION_ORDER_KEY)
    if not order_id:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = await CheckoutRepo.get_order_any(session, order_id)
    if not order or not order.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    if order.status != "pending_payment":
        # если юзер пытается платить с draft — значит он не прошёл checkout
        raise HTTPException(status_code=400, detail=f"Order not ready for payment (status={order.status})")

    CartService.recalc(order)

    cfg = _two_co_cfg(request)

    payment = Payment(
        order_id=order.id,
        provider="2checkout",
        status="created",
        amount=order.total,
        currency=order.currency,
    )
    await PaymentRepo.create(session, payment)

    url = TwoCOService.build_hosted_checkout_url(
        cfg,
        order_id=order.id,
        total=Decimal(order.total),
        currency=order.currency,
        title="NOIRID order",
    )

    payment.status = "redirected"
    await session.commit()

    return {"redirect_url": url}
