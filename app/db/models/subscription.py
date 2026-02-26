# app/models/subscription.py
from __future__ import annotations
import uuid

from sqlalchemy import String, DateTime, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class EmailSubscription(Base):
    __tablename__ = "email_subscriptions"
    __table_args__ = (UniqueConstraint("email", name="uq_email_subscriptions_email"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="confirmed")

    source: Mapped[str | None] = mapped_column(String(64))
    page_path: Mapped[str | None] = mapped_column(String(256))
    referrer: Mapped[str | None] = mapped_column(Text)

    utm_source: Mapped[str | None] = mapped_column(String(128))
    utm_medium: Mapped[str | None] = mapped_column(String(128))
    utm_campaign: Mapped[str | None] = mapped_column(String(128))
    utm_content: Mapped[str | None] = mapped_column(String(128))
    utm_term: Mapped[str | None] = mapped_column(String(128))

    user_agent: Mapped[str | None] = mapped_column(Text)
    accept_language: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)