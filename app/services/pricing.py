from __future__ import annotations

from decimal import Decimal

from app.db.models.product import Product, Variant


class PricingService:
    @staticmethod
    def calc_unit_price(product: Product, variant: Variant | None) -> Decimal:
        base = product.base_price or Decimal("0.00")
        delta = (variant.price_delta if variant else Decimal("0.00")) or Decimal("0.00")
        return (base + delta).quantize(Decimal("0.01"))
