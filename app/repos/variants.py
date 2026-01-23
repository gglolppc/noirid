from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product import Variant


class VariantsRepo:
    @staticmethod
    async def list_active(session: AsyncSession) -> list[Variant]:
        stmt = (
            select(Variant)
            .where(Variant.is_active.is_(True))
            .order_by(Variant.device_brand.asc(), Variant.device_model.asc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().unique().all())
