from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_async_session
from app.repos.support import SupportRepo

router = APIRouter(tags=["pages"])


@router.get("/about", include_in_schema=False)
async def about_page(request: Request):
    return templates.TemplateResponse("pages/about.html", {"request": request})


@router.get("/delivery", include_in_schema=False)
async def delivery_page(request: Request):
    return templates.TemplateResponse("pages/delivery.html", {"request": request})


@router.get("/support", include_in_schema=False)
async def support_page(request: Request):
    return templates.TemplateResponse("pages/support.html", {"request": request, "success": False})


@router.post("/support", include_in_schema=False)
async def support_submit(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    name: str = Form(...),
    email: str = Form(...),
    order_id: str | None = Form(default=None),
    question: str = Form(...),
):
    await SupportRepo.create(
        session,
        name=name.strip(),
        email=email.strip(),
        order_id=(order_id.strip() if order_id else None),
        question=question.strip(),
    )
    await session.commit()
    return templates.TemplateResponse("pages/support.html", {"request": request, "success": True})


@router.get("/check-order", include_in_schema=False)
async def check_order_page(request: Request):
    return templates.TemplateResponse("pages/check_order.html", {"request": request})
