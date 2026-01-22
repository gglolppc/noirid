from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from app.schemas.order_status import OrderStatusOut

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/{order_id}/status", response_model=OrderStatusOut)
async def order_status(order_id: str, session: AsyncSession = Depends(get_async_session)):
    order = await CheckoutRepo.get_order_any(session, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderStatusOut(
        order_id=order.id,
        status=order.status,
        payment_status=getattr(order, "payment_status", "unpaid"),
    )
