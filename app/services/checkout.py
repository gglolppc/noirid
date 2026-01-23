from __future__ import annotations

import logging

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
        previous_status = order.status
        order.status = "pending_payment"
        if previous_status != order.status:
            logging.getLogger("orders").info(
                "Order status changed | order_id=%s | from=%s | to=%s",
                order.id,
                previous_status,
                order.status,
            )
