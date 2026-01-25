from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid
from sqlalchemy import or_
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
        # Очищаем входные данные
        clean_id = str(order_id).strip()

        # Собираем условия поиска
        filters = [Order.id == clean_id]

        # Если это валидный UUID, ищем и по нему (на случай разных типов в драйвере)
        try:
            uuid_val = uuid.UUID(clean_id)
            filters.append(Order.id == str(uuid_val))
        except (ValueError, TypeError):
            pass

        stmt = (
            select(Order)
            .where(or_(*filters))
            .options(selectinload(Order.items))
        )
        res = await session.execute(stmt)
        return res.scalars().unique().first()
