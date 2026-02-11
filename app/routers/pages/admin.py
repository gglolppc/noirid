from __future__ import annotations

from math import ceil

from decimal import Decimal
import json

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal
from app.core.templates import templates
from app.db.models.product import Product, Variant
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
    status: Literal["pending_payment", "paid"] | None = None,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    page = max(page, 1)
    total = await OrdersRepo.count(session, status=status)
    total_pages = max(ceil(total / PER_PAGE), 1)
    page = min(page, total_pages)

    orders = await OrdersRepo.list_paginated(
        session,
        offset=(page - 1) * PER_PAGE,
        limit=PER_PAGE,
        status=status,
    )

    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "orders": orders,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "status": status,
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
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "product": None,
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
    currency: str = Form(default="EUR"),
    is_active: bool = Form(default=False),
    image_urls: list[str] = Form(default=[]),
    personalization_schema: str | None = Form(default=None),
):
    personalization_payload = _parse_personalization_schema(personalization_schema)
    product = Product(
        title=title.strip(),
        slug=slug.strip(),
        description=description.strip() if description else None,
        base_price=Decimal(base_price),
        currency=currency.strip().upper(),
        is_active=is_active,
        personalization_schema=personalization_payload,
        images=_normalize_product_images(image_urls),
    )
    session.add(product)

    await session.commit()
    return RedirectResponse("/admin/products", status_code=303)


@router.get("/products/{product_id}/edit", include_in_schema=False)
async def admin_product_edit(
    request: Request,
    product_id: int,
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    product = (await session.execute(select(Product).where(Product.id == product_id))).scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "product": product,
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
    currency: str = Form(default="EUR"),
    is_active: bool = Form(default=False),
    image_urls: list[str] = Form(default=[]),
    personalization_schema: str | None = Form(default=None),
):
    product = (await session.execute(select(Product).where(Product.id == product_id))).scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    personalization_payload = _parse_personalization_schema(personalization_schema)
    product.title = title.strip()
    product.slug = slug.strip()
    product.description = description.strip() if description else None
    product.base_price = Decimal(base_price)
    product.currency = currency.strip().upper()
    product.is_active = is_active
    product.personalization_schema = personalization_payload
    product.images = _normalize_product_images(image_urls)

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


def _list_media_images(current_path: Path, query: str = "") -> list[dict[str, str]]:
    query = query.strip().lower()
    images: list[dict[str, str]] = []
    for path in sorted(current_path.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            continue
        url = _url_for_media(path)
        if query and query not in path.name.lower() and query not in url.lower():
            continue
        images.append({"url": url})
    return images


def _normalize_product_images(image_urls: list[str]) -> list[dict[str, str]]:
    seen = set()
    normalized: list[dict[str, str]] = []
    for url in image_urls:
        cleaned = url.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append({"id": len(normalized), "url": cleaned})
    return normalized


from typing import Any, Dict
import json
from fastapi import HTTPException


def _parse_personalization_schema(raw_schema: str | None) -> Dict[str, Dict[str, Any]]:
    if raw_schema is None or not raw_schema.strip():
        return {}

    try:
        data = json.loads(raw_schema)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid personalization schema JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Personalization schema must be a JSON object")

    parsed: Dict[str, Dict[str, Any]] = {}

    for key, value in data.items():
        if not isinstance(key, str):
            raise HTTPException(status_code=400, detail="Personalization schema keys must be strings")

        # Логика поддержки двух форматов
        if isinstance(value, int):
            # Старый формат: {"word": 5} -> превращаем в {"limit": 5, "placeholder": "Type here..."}
            limit = value
            placeholder = "Type here..."
        elif isinstance(value, dict):
            # Новый формат: {"word": {"limit": 5, "placeholder": "ex. NOIR"}}
            limit = value.get("limit")
            placeholder = value.get("placeholder", "Type here...")

            if not isinstance(limit, int):
                raise HTTPException(
                    status_code=400,
                    detail=f"Limit for '{key}' must be an integer inside the object",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Value for '{key}' must be an integer or an object with 'limit'",
            )

        if limit < 1:
            raise HTTPException(
                status_code=400,
                detail=f"Limit for '{key}' must be greater than 0",
            )

        # Всегда возвращаем унифицированную структуру
        parsed[key] = {
            "limit": limit,
            "placeholder": placeholder
        }

    return parsed

async def _update_products_for_image_change(
    session: AsyncSession,
    old_url: str,
    new_url: str | None = None,
) -> None:
    products = (await session.execute(select(Product))).scalars().all()
    for product in products:
        if not product.images:
            continue
        updated = []
        changed = False
        for entry in product.images:
            url = entry.get("url")
            if url == old_url:
                changed = True
                if new_url:
                    updated.append({"id": len(updated), "url": new_url})
                continue
            updated.append({"id": len(updated), "url": url})
        if changed:
            product.images = updated


@router.get("/media", include_in_schema=False)
async def admin_media_library(
    request: Request,
    admin_user=Depends(require_admin),
    path: str | None = None,
    q: str | None = None,
):
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    current_path = _safe_media_path(path or "")
    if not current_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    folders = sorted([p for p in current_path.iterdir() if p.is_dir()], key=lambda p: p.name.lower())

    query = (q or "").strip().lower()
    images = _list_media_images(current_path, query)

    folder_parts = [part for part in (path or "").split("/") if part]
    return templates.TemplateResponse(
        "admin/media_library.html",
        {
            "request": request,
            "images": images,
            "admin_user": admin_user,
            "folders": folders,
            "current_path": path or "",
            "folder_parts": folder_parts,
            "query": q or "",
            "MEDIA_ROOT": MEDIA_ROOT,
        },
    )


@router.get("/media/images", include_in_schema=False)
async def admin_media_images(
    request: Request,
    admin_user=Depends(require_admin),
    folder: str | None = None,
    q: str | None = None,
):
    current_path = _safe_media_path(folder or "")
    if not current_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    images = _list_media_images(current_path, q or "")
    return JSONResponse({"images": images})


@router.post("/media/upload", include_in_schema=False)
async def admin_media_upload(
    request: Request,
    admin_user=Depends(require_admin),
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
    redirect_path = folder.strip("/") if folder else ""
    return RedirectResponse(f"/admin/media?path={redirect_path}", status_code=303)


@router.post("/media/folder", include_in_schema=False)
async def admin_media_create_folder(
    request: Request,
    admin_user=Depends(require_admin),
    folder: str = Form(...),
):
    target_dir = _safe_media_path(folder.strip("/"))
    target_dir.mkdir(parents=True, exist_ok=True)
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
        if target_path.exists():
            target_path.unlink()
        await _update_products_for_image_change(session, url)
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
    await _update_products_for_image_change(session, old_url, new_url)
    await session.commit()
    redirect_path = (current_path or "").strip("/")
    return RedirectResponse(f"/admin/media?path={redirect_path}", status_code=303)

@router.post("/orders/{order_id}/tracking", include_in_schema=False)
async def admin_add_tracking(
    request: Request,
    order_id: str,
    tracking_number: str = Form(...),
    admin_user=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    order = await OrdersRepo.get_by_id(session, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "paid":
        raise HTTPException(status_code=400, detail="Order is not paid")

    if order.tracking_number:
        raise HTTPException(status_code=400, detail="Tracking already set")

    order.tracking_number = tracking_number.strip()
    order.tracking_email_sent_at = None
    await session.commit()

    return RedirectResponse("/admin/orders", status_code=303)