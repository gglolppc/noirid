from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.cart import CartRepo
from app.repos.checkout import CheckoutRepo
from app.services.cart import CartService

router = APIRouter(prefix="/checkout", tags=["pages"])

SESSION_ORDER_KEY = "order_id"


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def checkout_page(request: Request, session: AsyncSession = Depends(get_async_session)):
    order_id = request.session.get(SESSION_ORDER_KEY)
    order = await CheckoutRepo.get_order_any(session, order_id) if order_id else None

    if order and order.payment_status == "paid":
        request.session.pop(SESSION_ORDER_KEY, None)
        order = None

    if order and order.status != "draft":
        draft = await CartRepo.create_order(session, currency=order.currency or "EUR")
        await CartRepo.clone_items(session, order, draft)
        request.session[SESSION_ORDER_KEY] = draft.id
        order = draft

    if order:
        CartService.recalc(order)
        await session.commit()

    return templates.TemplateResponse(
        "pages/checkout.html",
        {
            "request": request,
            "order": order,
            "subtotal": (order.subtotal if order else Decimal("0.00")),
            "total": (order.total if order else Decimal("0.00")),
            "currency": (order.currency if order else "EUR"),
        },
    )
