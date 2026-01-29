from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable

def _static_url_to_path(static_dir: Path, url: str) -> Path:
    rel = url.removeprefix("/static/").lstrip("/")
    return static_dir / rel

def _is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False

def persist_preview_files(
    *,
    order_id: str,
    items_data: Iterable[dict],
    static_dir: Path,
) -> list[dict[str, str]]:
    """
    items_data: [{"id": "<item_id>", "url": "<preview_url>"}]
    returns: [{"id": "<item_id>", "new_url": "<new_static_url>"}]
    """
    mockups_dir = static_dir / "out" / "mockups"
    orders_dir = static_dir / "out" / "orders" / order_id
    orders_dir.mkdir(parents=True, exist_ok=True)

    updates: list[dict[str, str]] = []

    for it in items_data:
        item_id = (it.get("id") or "").strip()
        url = (it.get("url") or "").strip()

        if not item_id:
            continue
        if not url.startswith("/static/out/mockups/"):
            continue

        src = _static_url_to_path(static_dir, url)

        if not _is_under(src, mockups_dir):
            continue
        if not src.is_file():
            continue

        ext = src.suffix.lower() or ".webp"
        dst = orders_dir / f"{item_id}{ext}"

        tmp = orders_dir / f".{item_id}{ext}.tmp.{os.getpid()}"
        try:
            shutil.copy2(src, tmp)
            tmp.replace(dst)  # atomic rename on same filesystem
        finally:
            # если copy2 успел создать tmp, но replace не произошёл
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass

        new_url = f"/static/out/orders/{order_id}/{dst.name}"
        updates.append({"id": item_id, "new_url": new_url})

    return updates
