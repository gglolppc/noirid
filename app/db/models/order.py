from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # draft -> pending_payment -> paid (завтра будет)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)

    currency: Mapped[str] = mapped_column(String(8), default="USD")

    # контакты
    customer_email: Mapped[str | None] = mapped_column(String(320), default=None, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(200), default=None)
    customer_phone: Mapped[str | None] = mapped_column(String(40), default=None)

    # адрес доставки одним JSON (быстро, гибко)
    shipping_address: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=True)

    # суммы
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payment_status: Mapped[str] = mapped_column(String(32), default="unpaid", index=True)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("variants.id", ondelete="RESTRICT"), index=True, default=None)

    title_snapshot: Mapped[str] = mapped_column(String(300))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    qty: Mapped[int] = mapped_column(Integer, default=1)

    personalization_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    order: Mapped["Order"] = relationship(back_populates="items")
