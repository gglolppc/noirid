from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.content import ContentRepo
from app.repos.products import ProductsRepo
from sqlalchemy import select, func
from app.db.models.product import Product
import random

HERO_IMAGES = [
    "/static/img/heroes/noir1.webp",
    "/static/img/heroes/noir6.webp",
]

router = APIRouter(tags=["pages"])


@router.get("/", include_in_schema=False)
async def home(request: Request, session: AsyncSession = Depends(get_async_session)):
    hero_img = random.choice(HERO_IMAGES)

    q = (
        select(Product)
        .where(Product.is_active.is_(True))
        .order_by(func.random())
        .limit(1)
    )
    products = (await session.execute(q)).scalars().first()


    return templates.TemplateResponse(
        "pages/home.html",
        {"request": request, "hero_img": hero_img, "featured_product": products},
    )
