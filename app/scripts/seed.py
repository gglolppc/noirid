from __future__ import annotations

import asyncio
import importlib
import os
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.product import Product, Variant
from app.services.auth import hash_password


# ---------- helpers ----------

async def _truncate_all_tables(session: AsyncSession) -> None:
    """
    Полная очистка БД (dev): TRUNCATE всех таблиц public, кроме alembic_version.
    Это решает вечные FK RESTRICT / order_items -> variants и т.п.
    """
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

    # TRUNCATE "t1","t2" RESTART IDENTITY CASCADE
    quoted = ", ".join(f'"{t}"' for t in tables)
    await session.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE;"))


def _try_import(path: str):
    try:
        mod_name, attr = path.rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr)
    except Exception:
        return None


async def _ensure_admin(session: AsyncSession) -> None:
    """
    Пытается создать админа для разных вариантов твоих таблиц.
    Если ни один не подошёл — просто молча пропускает.
    """
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    pwd_hash = hash_password(admin_password)

    # сюда можешь добавлять свои реальные модели при желании
    candidates = [
        "app.db.models.user.User",
        "app.db.models.admin.AdminUser",
        "app.db.models.admin.Admin",
    ]

    Model = None
    for p in candidates:
        Model = _try_import(p)
        if Model is not None:
            break

    if Model is None:
        print("seed: admin model not found, skipped")
        return

    # Найти существующего
    # username/email — самые частые варианты
    where_clause = None
    if hasattr(Model, "username"):
        where_clause = (Model.username == admin_username)
    elif hasattr(Model, "email"):
        where_clause = (Model.email == admin_username)

    if where_clause is None:
        print(f"seed: admin model {Model.__name__} has no username/email field, skipped")
        return

    existing = await session.execute(select(Model).where(where_clause))
    if existing.scalar_one_or_none():
        return

    # Собираем поля под твой конкретный User/Admin
    payload: dict[str, Any] = {}

    if hasattr(Model, "username"):
        payload["username"] = admin_username
    if hasattr(Model, "email"):
        payload["email"] = admin_username

    # пароль
    if hasattr(Model, "password_hash"):
        payload["password_hash"] = pwd_hash
    elif hasattr(Model, "hashed_password"):
        payload["hashed_password"] = pwd_hash
    elif hasattr(Model, "password"):
        payload["password"] = pwd_hash  # на всякий, если ты так назвал (не рекомендую)

    # роли/флаги
    if hasattr(Model, "role"):
        payload["role"] = "admin"
    if hasattr(Model, "is_admin"):
        payload["is_admin"] = True
    if hasattr(Model, "is_superuser"):
        payload["is_superuser"] = True
    if hasattr(Model, "is_active"):
        payload["is_active"] = True

    session.add(Model(**payload))
    print(f"seed: admin created in {Model.__name__} (login={admin_username})")


# ---------- seed ----------

async def seed() -> None:
    clean = os.getenv("SEED_CLEAN", "1") == "1"

    async with AsyncSessionLocal() as session:
        if clean:
            await _truncate_all_tables(session)

        # --- products ---
        p1 = Product(
            slug="noir-initials-case",
            title="NOIR Initials Case",
            description="Minimal black-on-black. Your initials, discreet.",
            base_price=Decimal("24.00"),
            currency="USD",
            personalization_schema={"initials": 4, "number": 6},
            images=[{"id": "0", "url": "/static/img/demo/case1.webp"}],
        )

        p2 = Product(
            slug="noir-plate-case",
            title="NOIR Plate Case",
            description="Plate style. Clean, sharp, readable.",
            base_price=Decimal("26.00"),
            currency="USD",
            personalization_schema={"initials": 3, "number": 8},
            images=[{"id": "0", "url": "/static/img/demo/case2.webp"}],
        )

        # ВАЖНО: uq_variant_device = (device_brand, device_model) уникальны на всю таблицу.
        # Поэтому не повторяй одну и ту же пару бренд+модель в других вариантах.
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

        # --- admin ---
        await _ensure_admin(session)

        await session.commit()

        res = await session.execute(select(Product).order_by(Product.id))
        print("Seeded products:", [p.slug for p in res.scalars().all()])


if __name__ == "__main__":
    asyncio.run(seed())
