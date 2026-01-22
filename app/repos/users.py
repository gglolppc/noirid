from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UsersRepo:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
        res = await session.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        res = await session.execute(select(User).where(User.username == username))
        return res.scalar_one_or_none()

    @staticmethod
    async def list_paginated(session: AsyncSession, offset: int, limit: int) -> list[User]:
        res = await session.execute(
            select(User).order_by(User.id.asc()).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    @staticmethod
    async def count(session: AsyncSession) -> int:
        res = await session.execute(select(func.count()).select_from(User))
        return int(res.scalar_one())
