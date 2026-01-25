from __future__ import annotations

import asyncio
import os
from decimal import Decimal

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.db.models.product import Product, Variant
from app.db.models.content import ContentBlock
from app.db.models.user import User
from app.services.auth import hash_password


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # очистка (для dev)
        await session.execute(delete(Variant))
        await session.execute(delete(Product))
        await session.execute(delete(ContentBlock))



        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")
        admin_user = await session.execute(select(User).where(User.username == admin_username))
        if not admin_user.scalar_one_or_none():
            session.add(
                User(
                    username=admin_username,
                    password_hash=hash_password(admin_password),
                    role="admin",
                )
            )
        await session.commit()

        # маленькая проверка
        res = await session.execute(select(Product).order_by(Product.id))
        print("Seeded products:", [p.slug for p in res.scalars().all()])


if __name__ == "__main__":
    asyncio.run(seed())
