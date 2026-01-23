from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.products import ProductsRepo
from app.repos.variants import VariantsRepo

router = APIRouter(prefix="/p", tags=["pages"])


@router.get("/{slug}", include_in_schema=False)
async def product_detail(slug: str, request: Request, session: AsyncSession = Depends(get_async_session)):
    product = await ProductsRepo.get_by_slug(session, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    variants = await VariantsRepo.list_active(session)
    variants_payload = [
        {
            "id": v.id,
            "brand": v.device_brand,
            "model": v.device_model,
            "price_delta": float(v.price_delta or 0),
        }
        for v in variants
    ]

    return templates.TemplateResponse(
        "pages/product.html",
        {
            "request": request,
            "product": product,
            "variants_payload": variants_payload,
        },
    )
