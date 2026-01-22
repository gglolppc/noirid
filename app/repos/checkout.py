from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.order import Order


class CheckoutRepo:
    @staticmethod
    async def get_draft_order(session: AsyncSession, order_id: str) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.status == "draft")
            .options(selectinload(Order.items))
        )
        res = await session.execute(stmt)
        return res.scalars().unique().first()

    @staticmethod
    async def get_order_any(session: AsyncSession, order_id: str) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        res = await session.execute(stmt)
        return res.scalars().unique().first()
