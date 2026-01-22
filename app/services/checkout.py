from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.schemas.checkout import CheckoutCreateOrderIn
from app.services.cart import CartService


class CheckoutService:
    @staticmethod
    def fill_customer_and_address(order: Order, data: CheckoutCreateOrderIn) -> None:
        order.customer_email = str(data.email)
        order.customer_name = data.name
        order.customer_phone = data.phone
        order.shipping_address = data.shipping_address.model_dump()

    @staticmethod
    def finalize_for_payment(order: Order) -> None:
        # пересчитать суммы (на всякий случай)
        CartService.recalc(order)
        order.status = "pending_payment"
