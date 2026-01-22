from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class ShippingAddressIn(BaseModel):
    country: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=1, max_length=120)
    line1: str = Field(min_length=3, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    postal_code: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=500)


class CheckoutCreateOrderIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    shipping_address: ShippingAddressIn
