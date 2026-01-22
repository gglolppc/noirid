from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.templates import templates

router = APIRouter(prefix="/cart", tags=["pages"])


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def cart_page(request: Request):
    return templates.TemplateResponse("pages/cart.html", {"request": request})
