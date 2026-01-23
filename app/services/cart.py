from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.order import Order


class CartService:
    @staticmethod
    def recalc(order: Order) -> None:
        subtotal = Decimal("0.00")
        for it in order.items:
            line = (it.unit_price or Decimal("0.00")) * int(it.qty or 0)
            subtotal += line
        order.subtotal = subtotal.quantize(Decimal("0.01"))
        shipping_fee = Decimal(str(settings.standard_shipping_fee_usd or "0.00"))
        order.total = (order.subtotal + shipping_fee).quantize(Decimal("0.01"))
