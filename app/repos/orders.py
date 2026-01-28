from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order


class OrdersRepo:
    ALLOWED_STATUSES = {"pending_payment", "paid"}

    @staticmethod
    def _apply_status_filter(stmt, status: str | None):
        if status in OrdersRepo.ALLOWED_STATUSES:
            return stmt.where(Order.status == status)
        return stmt

    @staticmethod
    async def list_recent(session: AsyncSession, limit: int = 10, status: str | None = None) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
        stmt = OrdersRepo._apply_status_filter(stmt, status)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def list_paginated(
        session: AsyncSession,
        offset: int,
        limit: int,
        status: str | None = None,
    ) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).offset(offset).limit(limit)
        stmt = OrdersRepo._apply_status_filter(stmt, status)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def count(session: AsyncSession, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(Order)
        stmt = OrdersRepo._apply_status_filter(stmt, status)
        res = await session.execute(stmt)
        return int(res.scalar_one())

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: str) -> Order | None:
        res = await session.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_order_number(session: AsyncSession, order_number: str) -> Order | None:
        # Приводим к верхнему регистру на всякий случай
        clean_number = order_number.strip().upper()

        res = await session.execute(
            select(Order)
            .where(Order.order_number == clean_number)
            .options(selectinload(Order.items))
        )
        return res.scalar_one_or_none()
