from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import Payment


class PaymentRepo:
    @staticmethod
    async def create(session: AsyncSession, payment: Payment) -> Payment:
        session.add(payment)
        await session.flush()
        return payment

    @staticmethod
    async def list_for_order(session: AsyncSession, order_id: str) -> list[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def list_paginated(session: AsyncSession, offset: int, limit: int) -> list[Payment]:
        stmt = select(Payment).order_by(Payment.id.desc()).offset(offset).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def count(session: AsyncSession) -> int:
        res = await session.execute(select(func.count()).select_from(Payment))
        return int(res.scalar_one())

    @staticmethod
    async def get_latest_for_order(session: AsyncSession, order_id: str) -> Payment | None:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc()).limit(1)
        res = await session.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def get_by_provider_order(session: AsyncSession, provider: str, provider_order_number: str) -> Payment | None:
        stmt = select(Payment).where(
            Payment.provider == provider,
            Payment.provider_order_number == provider_order_number,
        ).limit(1)
        res = await session.execute(stmt)
        return res.scalars().first()
