from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo

router = APIRouter(prefix="/order", tags=["pages"])


@router.get("/{order_id}", include_in_schema=False)
async def order_status_page(
    order_id: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order = await CheckoutRepo.get_order_any(session, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return templates.TemplateResponse(
        "pages/order_status.html",
        {"request": request, "order": order},
    )
