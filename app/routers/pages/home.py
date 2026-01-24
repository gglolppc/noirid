from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.content import ContentRepo
from app.repos.products import ProductsRepo
from sqlalchemy import select, func
from app.db.models.product import Product

router = APIRouter(tags=["pages"])


@router.get("/", include_in_schema=False)
async def home(request: Request, session: AsyncSession = Depends(get_async_session)):
    hero_block = await ContentRepo.get_by_key(session, "home_hero")
    hero = hero_block.payload if hero_block else {
        "title": "NOIRID",
        "subtitle": "Discreet personalization.",
        "cta_text": "Catalog",
        "cta_href": "/catalog",
    }
    q = (
        select(Product)
        .where(Product.is_active.is_(True))
        .order_by(func.random())
        .limit(1)
    )
    products = (await session.execute(q)).scalars().first()
    # featured_block = await ContentRepo.get_by_key(session, "featured_products")
    # slugs = (featured_block.payload or {}).get("slugs", []) if featured_block else []
    # featured_products = await ProductsRepo.list_by_slugs(session, slugs)

    return templates.TemplateResponse(
        "pages/home.html",
        {"request": request, "hero": hero, "featured_product": products},
    )
