from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.products import ProductsRepo

router = APIRouter(prefix="/p", tags=["pages"])


@router.get("/{slug}", include_in_schema=False)
async def product_detail(slug: str, request: Request, session: AsyncSession = Depends(get_async_session)):
    product = await ProductsRepo.get_by_slug(session, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # дефолтный вариант: первый активный
    variants = [v for v in product.variants if v.is_active]
    default_variant = variants[0] if variants else None

    return templates.TemplateResponse(
        "pages/product.html",
        {"request": request, "product": product, "default_variant": default_variant},
    )
