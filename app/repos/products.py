from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.product import Product


class ProductsRepo:
    @staticmethod
    async def list_active(session: AsyncSession) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.is_active.is_(True))
            .options(selectinload(Product.images), selectinload(Product.variants))
            .order_by(Product.id.desc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().unique().all())

    @staticmethod
    async def get_by_slug(session: AsyncSession, slug: str) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.slug == slug, Product.is_active.is_(True))
            .options(selectinload(Product.images), selectinload(Product.variants))
        )
        res = await session.execute(stmt)
        return res.scalars().unique().first()

    @staticmethod
    async def list_by_slugs(session: AsyncSession, slugs: list[str]) -> list[Product]:
        if not slugs:
            return []
        stmt = (
            select(Product)
            .where(Product.slug.in_(slugs), Product.is_active.is_(True))
            .options(selectinload(Product.images), selectinload(Product.variants))
        )
        res = await session.execute(stmt)
        items = list(res.scalars().unique().all())

        # сохранить порядок как в slugs
        order = {s: i for i, s in enumerate(slugs)}
        items.sort(key=lambda p: order.get(p.slug, 10_000))
        return items
