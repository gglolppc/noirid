from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.products import ProductsRepo

router = APIRouter(prefix="/catalog", tags=["pages"])


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def catalog(request: Request, session: AsyncSession = Depends(get_async_session)):
    products = await ProductsRepo.list_active(session)
    return templates.TemplateResponse(
        "pages/catalog.html",
        {"request": request, "products": products},
    )
