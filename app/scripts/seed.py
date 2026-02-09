from __future__ import annotations

import asyncio
import os

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.services.auth import hash_password


async def seed_admin() -> None:
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin875421")

    async with AsyncSessionLocal() as session:
        # не триггерим лишний autoflush, хоть тут и нечего флашить
        with session.no_autoflush:
            res = await session.execute(select(User).where(User.username == admin_username))
            existing = res.scalar_one_or_none()

        if existing:
            print(f"Admin already exists: {admin_username}")
            return

        session.add(
            User(
                username=admin_username,
                password_hash=hash_password(admin_password),
                role="admin",
            )
        )
        await session.commit()
        print(f"Admin created: {admin_username}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
