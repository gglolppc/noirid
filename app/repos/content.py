from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.content import ContentBlock


class ContentRepo:
    @staticmethod
    async def get_by_key(session: AsyncSession, key: str) -> ContentBlock | None:
        stmt = select(ContentBlock).where(ContentBlock.key == key)
        res = await session.execute(stmt)
        return res.scalars().first()
