from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from sqlalchemy.dialects.postgresql import JSONB


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32), default="2checkout")  # "2checkout"
    status: Mapped[str] = mapped_column(String(32), default="created")      # created/redirected/paid/failed

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(8))

    # что вернул 2CO
    provider_order_number: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    provider_invoice_id: Mapped[str | None] = mapped_column(String(64), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order")

    provider_message_type: Mapped[str | None] = mapped_column(String(64), default=None)
    provider_order_status: Mapped[str | None] = mapped_column(String(64), default=None)
    provider_invoice_status: Mapped[str | None] = mapped_column(String(64), default=None)
    provider_approve_status: Mapped[str | None] = mapped_column(String(64), default=None)

    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_payments_provider_order_unique", "provider", "provider_order_number", unique=False),
    )
