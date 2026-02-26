# app/routers/marketing.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.db.models.subscription import EmailSubscription

router = APIRouter(prefix="/api", tags=["marketing"])

def norm_email(v: str) -> str:
    return v.strip().lower()

@router.post("/subscribe")
async def subscribe(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    email: str = Form(...),
    source: str | None = Form(default="footer_form"),
    page_path: str | None = Form(default=None),
    utm_source: str | None = Form(default=None),
    utm_medium: str | None = Form(default=None),
    utm_campaign: str | None = Form(default=None),
    utm_content: str | None = Form(default=None),
    utm_term: str | None = Form(default=None),
):
    email_n = norm_email(email)

    existing = await session.scalar(
        select(EmailSubscription).where(EmailSubscription.email == email_n)
    )
    if existing:
        return JSONResponse({"success": True, "already": True})

    row = EmailSubscription(
        email=email_n,
        source=source,
        page_path=page_path,
        referrer=request.headers.get("referer"),
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_content=utm_content,
        utm_term=utm_term,
        user_agent=request.headers.get("user-agent"),
        accept_language=request.headers.get("accept-language"),
        status="confirmed",  # MVP: сразу confirmed, без писем
    )
    session.add(row)
    await session.commit()

    return JSONResponse({"success": True})