from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from uuid import UUID

from app.repos.orders import OrdersRepo

router = APIRouter(prefix="/order", tags=["pages"])


@router.get("/{order_number}", include_in_schema=False)  # Изменили здесь
async def order_status_page(
        order_number: str,  # Теперь совпадает
        request: Request,
        session: AsyncSession = Depends(get_async_session),
):
    order = await OrdersRepo.get_by_order_number(session, order_number)

    # Если заказ не найден, лучше сразу выдать 404 или редирект,
    # чтобы шаблон не упал при попытке прочитать order.status
    if not order:
        return templates.TemplateResponse("pages/404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse(
        "pages/order_status.html",
        {
            "request": request,
            "order": order,
            "order_number": order_number  # Передаем в шаблон красивый номер
        },
    )