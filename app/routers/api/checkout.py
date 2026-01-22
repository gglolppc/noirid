from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from app.schemas.checkout import CheckoutCreateOrderIn
from app.services.checkout import CheckoutService

router = APIRouter(prefix="/api/checkout", tags=["checkout"])

SESSION_ORDER_KEY = "order_id"


@router.post("/create-order")
async def create_order(
    payload: CheckoutCreateOrderIn,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order_id = request.session.get(SESSION_ORDER_KEY)
    if not order_id:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = await CheckoutRepo.get_draft_order(session, order_id)
    if not order:
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=400, detail="Cart is empty")

    if not order.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # заполняем контакты + адрес
    CheckoutService.fill_customer_and_address(order, payload)

    # переводим в pending_payment
    CheckoutService.finalize_for_payment(order)

    await session.commit()

    return {"order_id": order.id, "status": order.status}
