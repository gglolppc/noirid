from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repos.cart import CartRepo
from app.repos.checkout import CheckoutRepo
from app.schemas.checkout import CheckoutCreateOrderIn
from app.services.checkout import CheckoutService

router = APIRouter(prefix="/api/checkout", tags=["checkout"])

SESSION_ORDER_KEY = "order_id"
log = logging.getLogger("orders")


@router.post("/create-order")
async def create_order(
    payload: CheckoutCreateOrderIn,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order_id = request.session.get(SESSION_ORDER_KEY)
    if not order_id:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = await CheckoutRepo.get_order_any(session, order_id)
    if not order:
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=400, detail="Cart is empty")

    if order.payment_status == "paid":
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=400, detail="Cart is empty")

    if order.status != "draft":
        draft = await CartRepo.create_order(session, currency=order.currency or "EUR")
        await CartRepo.clone_items(session, order, draft)
        request.session[SESSION_ORDER_KEY] = draft.id
        order = draft

    if not order.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # заполняем контакты + адрес
    CheckoutService.fill_customer_and_address(order, payload)

    # переводим в pending_payment
    CheckoutService.finalize_for_payment(order)

    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        user_id = request.session.get("user_id", "anonymous")
        log.error(
            "Failed to create order | user_id=%s | order_id=%s | error=%s",
            user_id,
            order.id,
            exc.__class__.__name__,
        )
        raise HTTPException(status_code=500, detail="Failed to create order") from exc

    return {"order_id": order.id, "status": order.status}
