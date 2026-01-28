from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order


def _static_url_to_path(static_dir: Path, url: str) -> Path:
    """
    Convert '/static/...' URL to filesystem path under static_dir.
    """
    # url expected like: /static/out/mockups/....
    rel = url.removeprefix("/static/").lstrip("/")
    return (static_dir / rel)


def _is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def persist_order_previews(
    *,
    order: Order,
    static_dir: Path,
    session: AsyncSession | None = None,
) -> int:
    """
    Copies preview images from /static/out/mockups/... into /static/out/orders/<order_id>/...
    and rewrites OrderItem.preview_url accordingly.

    Returns number of updated items.
    """
    mockups_dir = static_dir / "out" / "mockups"
    orders_dir = static_dir / "out" / "orders" / str(order.id)
    orders_dir.mkdir(parents=True, exist_ok=True)

    updated = 0

    # order.items должны быть загружены (у тебя они обычно selectinload)
    for it in getattr(order, "items", []) or []:
        url = (getattr(it, "preview_url", None) or "").strip()
        if not url:
            continue

        # сохраняем только то, что пришло из mockups-кэша
        if not url.startswith("/static/out/mockups/"):
            continue

        src = _static_url_to_path(static_dir, url)

        # защита от кривого URL/попыток traversal
        if not _is_under(src, mockups_dir):
            continue

        if not src.exists() or not src.is_file():
            # файл мог быть уже почищен/не успел создаться
            continue

        # расширение берём из src (обычно webp)
        ext = src.suffix.lower() or ".webp"
        dst = orders_dir / f"{it.id}{ext}"

        # copy2 сохраняет метаданные (не критично, но норм)
        shutil.copy2(src, dst)

        it.preview_url = f"/static/out/orders/{order.id}/{dst.name}"
        updated += 1

    # session не обязателен: если order в сессии — изменения и так закоммитятся выше по стеку
    # но если хочешь явно:
    if session is not None:
        session.add(order)

    return updated
