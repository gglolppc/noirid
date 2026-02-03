# from __future__ import annotations
#
# from decimal import Decimal
#
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from app.db.models.order import Order
#
#
# class CartService:
#     @staticmethod
#     def recalc(order: Order) -> None:
#         subtotal = Decimal("0.00")
#         for it in order.items:
#             line = (it.unit_price or Decimal("0.00")) * int(it.qty or 0)
#             subtotal += line
#         order.subtotal = subtotal.quantize(Decimal("0.01"))
#         order.total = order.subtotal.quantize(Decimal("0.01"))

# app/services/cart.py

from decimal import Decimal, ROUND_HALF_UP

CASE_DISCOUNT_QTY = 2
CASE_DISCOUNT_RATE = Decimal("0.15")

def money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class CartService:
    @staticmethod
    def recalc(order) -> None:
        # subtotal товаров
        subtotal = Decimal("0.00")
        total_qty = 0

        for it in order.items or []:
            unit = it.unit_price or Decimal("0.00")
            qty = int(it.qty or 0)
            subtotal += unit * qty
            total_qty += qty

        subtotal = money(subtotal)

        # скидка: >= 2 чехлов (пока считаем, что все items — чехлы)
        discount = Decimal("0.00")
        reason = None

        if total_qty >= CASE_DISCOUNT_QTY:
            discount = money(subtotal * CASE_DISCOUNT_RATE)
            reason = "2_cases_15"

        order.subtotal = subtotal
        order.discount_amount = discount
        order.discount_reason = reason

        # если у тебя есть доставка — подставь
        shipping = getattr(order, "shipping_amount", None)
        if shipping is None:
            shipping = Decimal("0.00")

        order.total = money(order.subtotal - order.discount_amount + Decimal(shipping))
