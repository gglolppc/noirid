from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.support import SupportQuestion


class SupportRepo:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        name: str,
        email: str,
        order_id: str | None,
        question: str,
    ) -> SupportQuestion:
        item = SupportQuestion(
            customer_name=name,
            customer_email=email,
            order_id=order_id,
            question=question,
        )
        session.add(item)
        await session.flush()
        return item

    @staticmethod
    async def count(session: AsyncSession) -> int:
        res = await session.execute(select(func.count()).select_from(SupportQuestion))
        return int(res.scalar() or 0)

    @staticmethod
    async def list_paginated(session: AsyncSession, *, offset: int, limit: int) -> list[SupportQuestion]:
        stmt = select(SupportQuestion).order_by(SupportQuestion.created_at.desc()).offset(offset).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars())
