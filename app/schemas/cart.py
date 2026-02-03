from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, PositiveInt


class CartAddIn(BaseModel):
    product_id: PositiveInt
    variant_id: int | None = None
    qty: int = Field(default=1, ge=1, le=99)
    personalization: dict[str, Any] = Field(default_factory=dict)
    preview_url: str | None = None


class CartUpdateQtyIn(BaseModel):
    item_id: int
    qty: int = Field(ge=1, le=99)


class CartRemoveIn(BaseModel):
    item_id: int


class CartItemOut(BaseModel):
    id: int
    title: str
    qty: int
    unit_price: Decimal
    line_total: Decimal
    variant_id: int | None = None
    preview_url: str | None = None
    personalization: dict[str, Any] = Field(default_factory=dict)


class CartOut(BaseModel):
    order_id: str
    currency: str
    subtotal: Decimal
    total: Decimal
    discount_amount: Decimal = Decimal("0.00")
    discount_reason: str | None = None

    items: list[CartItemOut]

