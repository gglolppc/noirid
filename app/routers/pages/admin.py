from __future__ import annotations

from math import ceil

from decimal import Decimal

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.models.product import Product, ProductImage, Variant, product_image_links
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
MEDIA_ROOT = Path(__file__).resolve().parents[2] / "static" / "images"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


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
async def admin_products_list(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    products = (await session.execute(select(Product).order_by(Product.id.desc()))).scalars().all()
    return templates.TemplateResponse(
        "admin/products_list.html",
        {"request": request, "products": products, "admin_user": admin_user},
    )


@router.get("/products/new", include_in_schema=False)
async def admin_product_new(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    images = (await session.execute(select(ProductImage).order_by(ProductImage.id.desc()))).scalars().all()
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "product": None,
            "images": images,
            "media_folders": _list_media_folders(),
            "action_url": "/admin/products/new",
            "admin_user": admin_user,
        },
    )


@router.post("/products/new", include_in_schema=False)
async def admin_product_create(
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
        await session.execute(
            product_image_links.insert(),
            [{"product_id": product.id, "image_id": image_id} for image_id in image_ids],
        )

    await session.commit()
    return RedirectResponse("/admin/products", status_code=303)


@router.get("/products/{product_id}/edit", include_in_schema=False)
async def admin_product_edit(
    request: Request,
    product_id: int,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    product = (
        await session.execute(
            select(Product).where(Product.id == product_id).options(selectinload(Product.images))
        )
    ).scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    images = (await session.execute(select(ProductImage).order_by(ProductImage.id.desc()))).scalars().all()
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "product": product,
            "images": images,
            "media_folders": _list_media_folders(),
            "action_url": f"/admin/products/{product_id}/edit",
            "admin_user": admin_user,
        },
    )


@router.post("/products/{product_id}/edit", include_in_schema=False)
async def admin_product_update(
    request: Request,
    product_id: int,
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
    product = (
        await session.execute(
            select(Product).where(Product.id == product_id).options(selectinload(Product.images))
        )
    ).scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.title = title.strip()
    product.slug = slug.strip()
    product.description = description.strip() if description else None
    product.base_price = Decimal(base_price)
    product.currency = currency.strip().upper()
    product.is_active = is_active

    await session.execute(delete(product_image_links).where(product_image_links.c.product_id == product.id))
    if image_ids:
        await session.execute(
            product_image_links.insert(),
            [{"product_id": product.id, "image_id": image_id} for image_id in image_ids],
        )

    await session.commit()
    return RedirectResponse("/admin/products", status_code=303)


@router.post("/products/{product_id}/delete", include_in_schema=False)
async def admin_product_delete(
    request: Request,
    product_id: int,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    product = (await session.execute(select(Product).where(Product.id == product_id))).scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return RedirectResponse("/admin/products", status_code=303)


@router.get("/variants", include_in_schema=False)
async def admin_variants(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    variants = (await session.execute(select(Variant).order_by(Variant.id.desc()))).scalars().all()
    return templates.TemplateResponse(
        "admin/variants.html",
        {"request": request, "variants": variants, "admin_user": admin_user},
    )


@router.post("/variants", include_in_schema=False)
async def admin_create_variant(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    sku: str = Form(...),
    device_brand: str = Form(...),
    device_model: str = Form(...),
    price_delta: str = Form(default="0.00"),
    stock_qty: str | None = Form(default=None),
    is_active: bool = Form(default=False),
):
    stock_value = int(stock_qty) if stock_qty not in (None, "") else None
    variant = Variant(
        product_id=None,
        sku=sku.strip(),
        device_brand=device_brand.strip(),
        device_model=device_model.strip(),
        price_delta=Decimal(price_delta),
        stock_qty=stock_value,
        is_active=is_active,
    )
    session.add(variant)
    await session.commit()
    return RedirectResponse("/admin/variants", status_code=303)


@router.get("/variants/{variant_id}/edit", include_in_schema=False)
async def admin_variant_edit(
    request: Request,
    variant_id: int,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    variant = (await session.execute(select(Variant).where(Variant.id == variant_id))).scalars().first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return templates.TemplateResponse(
        "admin/variant_form.html",
        {"request": request, "variant": variant, "admin_user": admin_user},
    )


@router.post("/variants/{variant_id}/edit", include_in_schema=False)
async def admin_variant_update(
    request: Request,
    variant_id: int,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    sku: str = Form(...),
    device_brand: str = Form(...),
    device_model: str = Form(...),
    price_delta: str = Form(default="0.00"),
    stock_qty: str | None = Form(default=None),
    is_active: bool = Form(default=False),
):
    variant = (await session.execute(select(Variant).where(Variant.id == variant_id))).scalars().first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    variant.sku = sku.strip()
    variant.device_brand = device_brand.strip()
    variant.device_model = device_model.strip()
    variant.price_delta = Decimal(price_delta)
    variant.stock_qty = int(stock_qty) if stock_qty not in (None, "") else None
    variant.is_active = is_active
    await session.commit()
    return RedirectResponse("/admin/variants", status_code=303)


@router.post("/variants/{variant_id}/delete", include_in_schema=False)
async def admin_variant_delete(
    request: Request,
    variant_id: int,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    variant = (await session.execute(select(Variant).where(Variant.id == variant_id))).scalars().first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    await session.delete(variant)
    await session.commit()
    return RedirectResponse("/admin/variants", status_code=303)


def _safe_media_path(relative_path: str) -> Path:
    if not relative_path:
        return MEDIA_ROOT
    safe_path = (MEDIA_ROOT / relative_path).resolve()
    if not str(safe_path).startswith(str(MEDIA_ROOT.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    return safe_path


def _url_for_media(path: Path) -> str:
    rel = path.relative_to(MEDIA_ROOT).as_posix()
    return f"/static/images/{rel}"


def _list_media_folders() -> list[str]:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    folders = []
    for path in MEDIA_ROOT.rglob("*"):
        if path.is_dir():
            rel = path.relative_to(MEDIA_ROOT).as_posix()
            if rel:
                folders.append(rel)
    return sorted(folders)


@router.get("/media", include_in_schema=False)
async def admin_media_library(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    path: str | None = None,
    q: str | None = None,
):
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    current_path = _safe_media_path(path or "")
    if not current_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    folders = sorted([p for p in current_path.iterdir() if p.is_dir()], key=lambda p: p.name.lower())

    query = (q or "").strip().lower()
    images_query = select(ProductImage).order_by(ProductImage.id.desc())
    if path:
        prefix = f"/static/images/{path.strip('/')}/"
        images_query = images_query.where(ProductImage.url.like(f"{prefix}%"))
    if query:
        images_query = images_query.where(ProductImage.url.ilike(f"%{query}%"))
    images = (await session.execute(images_query)).scalars().all()
    products = (await session.execute(select(Product).order_by(Product.title.asc()))).scalars().all()

    folder_parts = [part for part in (path or "").split("/") if part]
    return templates.TemplateResponse(
        "admin/media_library.html",
        {
            "request": request,
            "images": images,
            "products": products,
            "admin_user": admin_user,
            "folders": folders,
            "current_path": path or "",
            "folder_parts": folder_parts,
            "query": q or "",
            "MEDIA_ROOT": MEDIA_ROOT,
        },
    )


@router.post("/media/upload", include_in_schema=False)
async def admin_media_upload(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    image: UploadFile = File(...),
    folder: str | None = Form(default=None),
):
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    if not image.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    ext = Path(image.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    target_dir = _safe_media_path(folder or "")
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / image.filename
    counter = 1
    while target_path.exists():
        target_path = target_dir / f"{target_path.stem}-{counter}{ext}"
        counter += 1

    contents = await image.read()
    target_path.write_bytes(contents)

    url = _url_for_media(target_path)
    existing = (await session.execute(select(ProductImage).where(ProductImage.url == url))).scalars().first()
    if not existing:
        session.add(ProductImage(url=url, sort=0))
    await session.commit()
    redirect_path = folder.strip("/") if folder else ""
    return RedirectResponse(f"/admin/media?path={redirect_path}", status_code=303)


@router.post("/media/folder", include_in_schema=False)
async def admin_media_create_folder(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    folder: str = Form(...),
):
    target_dir = _safe_media_path(folder.strip("/"))
    target_dir.mkdir(parents=True, exist_ok=True)
    await session.commit()
    redirect_path = folder.strip("/")
    return RedirectResponse(f"/admin/media?path={redirect_path}", status_code=303)


@router.post("/media/delete", include_in_schema=False)
async def admin_media_delete(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    target: str = Form(...),
    current_path: str | None = Form(default=None),
):
    target_path = _safe_media_path(target.strip("/"))
    if target_path.is_dir():
        if any(target_path.iterdir()):
            raise HTTPException(status_code=400, detail="Folder is not empty")
        target_path.rmdir()
    else:
        url = _url_for_media(target_path)
        image_record = (await session.execute(select(ProductImage).where(ProductImage.url == url))).scalars().first()
        if image_record:
            await session.execute(
                product_image_links.delete().where(product_image_links.c.image_id == image_record.id)
            )
            await session.delete(image_record)
        if target_path.exists():
            target_path.unlink()
    await session.commit()
    redirect_path = (current_path or "").strip("/")
    return RedirectResponse(f"/admin/media?path={redirect_path}", status_code=303)


@router.post("/media/rename", include_in_schema=False)
async def admin_media_rename(
    request: Request,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    source: str = Form(...),
    destination: str = Form(...),
    current_path: str | None = Form(default=None),
):
    source_path = _safe_media_path(source.strip("/"))
    destination_path = _safe_media_path(destination.strip("/"))
    if source_path.is_dir():
        raise HTTPException(status_code=400, detail="Folder rename is not supported")
    if destination_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.replace(destination_path)
    old_url = _url_for_media(source_path)
    new_url = _url_for_media(destination_path)
    image_record = (await session.execute(select(ProductImage).where(ProductImage.url == old_url))).scalars().first()
    if image_record:
        image_record.url = new_url
    await session.commit()
    redirect_path = (current_path or "").strip("/")
    return RedirectResponse(f"/admin/media?path={redirect_path}", status_code=303)
