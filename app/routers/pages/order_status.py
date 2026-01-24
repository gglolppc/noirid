from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from uuid import UUID
router = APIRouter(prefix="/order", tags=["pages"])


@router.get("/{order_id}", include_in_schema=False)
async def order_status_page(
    order_id: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        order_uuid = UUID(order_id)
    except ValueError:
        # даже не лезем в БД
        return templates.TemplateResponse(
            "pages/order_status.html",
            {"request": request, "order": None, "order_id": None},
        )
    order = await CheckoutRepo.get_order_any(session, order_id)
    return templates.TemplateResponse(
        "pages/order_status.html",
        {"request": request, "order": order, "order_id": order_id},
    )
