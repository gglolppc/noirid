from __future__ import annotations

from math import ceil

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.models.user import User
from app.db.session import get_async_session
from app.repos.orders import OrdersRepo
from app.repos.payments import PaymentRepo
from app.repos.users import UsersRepo
from app.services.auth import verify_password

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SESSION_KEY = "admin_user_id"
PER_PAGE = 20


async def require_admin(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> User:
    user_id = request.session.get(ADMIN_SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    user = await UsersRepo.get_by_id(session, int(user_id))
    if not user or user.role != "admin":
        request.session.pop(ADMIN_SESSION_KEY, None)
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return user


@router.get("/login", include_in_schema=False)
async def admin_login_page(request: Request):
    if request.session.get(ADMIN_SESSION_KEY):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login", include_in_schema=False)
async def admin_login(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    username: str = Form(...),
    password: str = Form(...),
):
    user = await UsersRepo.get_by_username(session, username.strip())
    if not user or user.role != "admin" or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=401,
        )
    request.session[ADMIN_SESSION_KEY] = user.id
    return RedirectResponse("/admin", status_code=303)


@router.get("/logout", include_in_schema=False)
async def admin_logout(request: Request):
    request.session.pop(ADMIN_SESSION_KEY, None)
    return RedirectResponse("/admin/login", status_code=303)


@router.get("", include_in_schema=False)
async def admin_dashboard(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    recent_orders = await OrdersRepo.list_recent(session, limit=10)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "recent_orders": recent_orders, "admin_user": admin_user},
    )


@router.get("/orders", include_in_schema=False)
async def admin_orders(
    request: Request,
    page: int = 1,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    page = max(page, 1)
    total = await OrdersRepo.count(session)
    total_pages = max(ceil(total / PER_PAGE), 1)
    page = min(page, total_pages)
    orders = await OrdersRepo.list_paginated(session, offset=(page - 1) * PER_PAGE, limit=PER_PAGE)
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "orders": orders,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "admin_user": admin_user,
        },
    )


@router.get("/orders/{order_id}", include_in_schema=False)
async def admin_order_detail(
    request: Request,
    order_id: str,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    order = await OrdersRepo.get_by_id(session, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    payments = await PaymentRepo.list_for_order(session, order_id)
    return templates.TemplateResponse(
        "admin/order_detail.html",
        {"request": request, "order": order, "payments": payments, "admin_user": admin_user},
    )


@router.get("/users", include_in_schema=False)
async def admin_users(
    request: Request,
    page: int = 1,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    page = max(page, 1)
    total = await UsersRepo.count(session)
    total_pages = max(ceil(total / PER_PAGE), 1)
    page = min(page, total_pages)
    users = await UsersRepo.list_paginated(session, offset=(page - 1) * PER_PAGE, limit=PER_PAGE)
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "users": users,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "admin_user": admin_user,
        },
    )


@router.get("/payments", include_in_schema=False)
async def admin_payments(
    request: Request,
    page: int = 1,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    page = max(page, 1)
    total = await PaymentRepo.count(session)
    total_pages = max(ceil(total / PER_PAGE), 1)
    page = min(page, total_pages)
    payments = await PaymentRepo.list_paginated(session, offset=(page - 1) * PER_PAGE, limit=PER_PAGE)
    return templates.TemplateResponse(
        "admin/payments.html",
        {
            "request": request,
            "payments": payments,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "admin_user": admin_user,
        },
    )
