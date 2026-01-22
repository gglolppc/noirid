from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order


class OrdersRepo:
    @staticmethod
    async def list_recent(session: AsyncSession, limit: int = 10) -> list[Order]:
        res = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(limit)
        )
        return list(res.scalars().all())

    @staticmethod
    async def list_paginated(session: AsyncSession, offset: int, limit: int) -> list[Order]:
        res = await session.execute(
            select(Order).order_by(Order.created_at.desc()).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    @staticmethod
    async def count(session: AsyncSession) -> int:
        res = await session.execute(select(func.count()).select_from(Order))
        return int(res.scalar_one())

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: str) -> Order | None:
        res = await session.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        return res.scalar_one_or_none()
