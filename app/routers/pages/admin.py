from __future__ import annotations

from math import ceil

from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.models.product import Product, ProductImage, Variant
from app.db.models.user import User
from app.db.session import get_async_session
from app.repos.orders import OrdersRepo
from app.repos.payments import PaymentRepo
from app.repos.support import SupportRepo
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


@router.get("/questions", include_in_schema=False)
async def admin_questions(
    request: Request,
    page: int = 1,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    page = max(page, 1)
    total = await SupportRepo.count(session)
    total_pages = max(ceil(total / PER_PAGE), 1)
    page = min(page, total_pages)
    questions = await SupportRepo.list_paginated(session, offset=(page - 1) * PER_PAGE, limit=PER_PAGE)
    return templates.TemplateResponse(
        "admin/questions.html",
        {
            "request": request,
            "questions": questions,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "admin_user": admin_user,
        },
    )


@router.get("/products", include_in_schema=False)
async def admin_products(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    products = (await session.execute(select(Product).order_by(Product.id.desc()))).scalars().all()
    images = (await session.execute(select(ProductImage).order_by(ProductImage.id.desc()))).scalars().all()
    variants = (await session.execute(select(Variant).order_by(Variant.id.desc()))).scalars().all()
    return templates.TemplateResponse(
        "admin/products.html",
        {
            "request": request,
            "products": products,
            "images": images,
            "variants": variants,
            "admin_user": admin_user,
        },
    )


@router.post("/products/create-product", include_in_schema=False)
async def admin_create_product(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    title: str = Form(...),
    slug: str = Form(...),
    description: str | None = Form(default=None),
    base_price: str = Form(...),
    currency: str = Form(default="USD"),
    is_active: bool = Form(default=False),
    image_ids: list[int] = Form(default=[]),
):
    product = Product(
        title=title.strip(),
        slug=slug.strip(),
        description=description.strip() if description else None,
        base_price=Decimal(base_price),
        currency=currency.strip().upper(),
        is_active=is_active,
    )
    session.add(product)
    await session.flush()

    if image_ids:
        stmt = select(ProductImage).where(ProductImage.id.in_(image_ids))
        images = (await session.execute(stmt)).scalars().all()
        for image in images:
            image.product_id = product.id

    await session.commit()
    return RedirectResponse("/admin/products", status_code=303)


@router.post("/products/create-variant", include_in_schema=False)
async def admin_create_variant(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    product_id: int = Form(...),
    sku: str = Form(...),
    device_brand: str = Form(...),
    device_model: str = Form(...),
    price_delta: str = Form(default="0.00"),
    stock_qty: str | None = Form(default=None),
    is_active: bool = Form(default=False),
):
    stock_value = int(stock_qty) if stock_qty not in (None, "") else None
    variant = Variant(
        product_id=product_id,
        sku=sku.strip(),
        device_brand=device_brand.strip(),
        device_model=device_model.strip(),
        price_delta=Decimal(price_delta),
        stock_qty=stock_value,
        is_active=is_active,
    )
    session.add(variant)
    await session.commit()
    return RedirectResponse("/admin/products", status_code=303)


@router.post("/products/create-image", include_in_schema=False)
async def admin_create_image(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    url: str = Form(...),
    sort: int = Form(default=0),
    product_id: str | None = Form(default=None),
):
    product_value = int(product_id) if product_id not in (None, "") else None
    image = ProductImage(
        url=url.strip(),
        sort=sort,
        product_id=product_value,
    )
    session.add(image)
    await session.commit()
    return RedirectResponse("/admin/products", status_code=303)
