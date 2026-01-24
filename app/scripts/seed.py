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

        p1 = Product(
            slug="noir-initials-case",
            title="NOIR Initials Case",
            description="Minimal black-on-black. Your initials, discreet.",
            base_price=Decimal("24.00"),
            currency="USD",
            personalization_schema={
                "text": {"max_len": 4, "fonts": ["Inter", "Cinzel"], "colors": ["#ffffff"]},
                "upload": {"required": False},
            },
        )
        p1.images = [{"id": 0, "url": "/static/img/demo/case1.webp"}]

        p2 = Product(
            slug="noir-plate-case",
            title="NOIR Plate Case",
            description="Plate style. Clean, sharp, readable.",
            base_price=Decimal("26.00"),
            currency="USD",
            personalization_schema={
                "text": {"max_len": 10, "fonts": ["Inter"], "colors": ["#ffffff"]},
                "upload": {"required": False},
            },
        )
        p2.images = [{"id": 0, "url": "/static/img/demo/case2.webp"}]

        variants = [
            Variant(sku="NOIR-INIT-IPH15P", device_brand="iPhone", device_model="15 Pro Max", price_delta=Decimal("0.00")),
            Variant(sku="NOIR-INIT-S23U", device_brand="Samsung", device_model="S23 Ultra", price_delta=Decimal("2.00")),
        ]

        home_hero = ContentBlock(
            key="home_hero",
            payload={
                "title": "NOIRID",
                "subtitle": "Discreet personalization. Dark aesthetics.",
                "cta_text": "Shop designs",
                "cta_href": "/catalog",
                "bg": "texture-black-1",
            },
        )

        featured = ContentBlock(
            key="featured_products",
            payload={"slugs": [p1.slug, p2.slug]},
        )

        session.add_all([p1, p2, home_hero, featured, *variants])

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
