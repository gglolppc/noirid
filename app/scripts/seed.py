from __future__ import annotations

import asyncio
import os
from decimal import Decimal
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.product import Product, Variant
from app.services.auth import hash_password


async def _truncate_all_tables(session: AsyncSession) -> None:
    res = await session.execute(
        text("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public' AND tablename <> 'alembic_version'
        ORDER BY tablename;
        """)
    )
    tables = [r[0] for r in res.all()]
    if not tables:
        return
    quoted = ", ".join(f'"{t}"' for t in tables)
    await session.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE;"))


async def _ensure_admin(session: AsyncSession) -> None:
    # Подстроимся под твою реальную модель User.
    # Если у тебя не User — скажешь, я поправлю под точную.
    from app.db.models.user import User  # <-- если у тебя другой путь/класс, поменяем

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")

    existing = await session.execute(select(User).where(User.username == admin_username))
    if existing.scalar_one_or_none():
        return

    session.add(
        User(
            username=admin_username,
            password_hash=hash_password(admin_password),
            role="admin",
        )
    )


async def seed() -> None:
    clean = os.getenv("SEED_CLEAN", "1") == "1"

    async with AsyncSessionLocal() as session:
        if clean:
            await _truncate_all_tables(session)

        p1 = Product(
            slug="noir-initials-case",
            title="NOIR Initials Case",
            description="Minimal black-on-black. Your initials, discreet.",
            base_price=Decimal("24.00"),
            currency="USD",
            personalization_schema={"initials": 4, "number": 6},
        )

        p2 = Product(
            slug="noir-plate-case",
            title="NOIR Plate Case",
            description="Plate style. Clean, sharp, readable.",
            base_price=Decimal("26.00"),
            currency="USD",
            personalization_schema={"initials": 3, "number": 8},
        )

        # Варианты прикрепляем к продукту через relationship "product"
        v1 = Variant(
            sku="NOIR-INIT-IPH15P",
            device_brand="iPhone",
            device_model="15 Pro Max",
            price_delta=Decimal("0.00"),
            stock_qty=None,
            is_active=True,
            product=p1,
        )

        v2 = Variant(
            sku="NOIR-INIT-S23U",
            device_brand="Samsung",
            device_model="S23 Ultra",
            price_delta=Decimal("2.00"),
            stock_qty=None,
            is_active=True,
            product=p1,
        )

        session.add_all([p1, p2, v1, v2])

        await _ensure_admin(session)

        await session.commit()

        res = await session.execute(select(Product).order_by(Product.id))
        print("Seeded products:", [p.slug for p in res.scalars().all()])


if __name__ == "__main__":
    asyncio.run(seed())
