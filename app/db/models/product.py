from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(8), default="USD")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    personalization_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    variants: Mapped[list["Variant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

    images: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )


class Variant(Base):
    __tablename__ = "variants"
    __table_args__ = (
        UniqueConstraint(
            "device_brand",
            "device_model",
            name="uq_variant_device",
        ),
        Index("ix_variant_brand_active", "device_brand", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    device_brand: Mapped[str] = mapped_column(String(100), nullable=False)
    device_model: Mapped[str] = mapped_column(String(150), nullable=False)

    price_delta: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))

    stock_qty: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped["Product"] = relationship(back_populates="variants")

