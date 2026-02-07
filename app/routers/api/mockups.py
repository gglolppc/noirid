from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.db.session import get_async_session
from app.db.models.product import Variant, Product  # <-- поправь импорт под себя

from app.services.mockup_engine import render_cached
from app.services.mockup_designs import DESIGNS
from app.services.mockup_models import MODEL_LAYOUTS


router = APIRouter(prefix="/api/mockups", tags=["mockups"])


APP_DIR = Path(__file__).resolve().parents[2]   # .../app
STATIC_DIR = APP_DIR / "static"

FONTS_DIR = STATIC_DIR / "fonts"
MOCKS_DIR = STATIC_DIR / "images" / "mocks"
CACHE_DIR = STATIC_DIR / "out" / "mockups"      # если хочешь кэш в static
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class MockupPreviewRequest(BaseModel):
    product_slug: str = Field(min_length=1, max_length=120)
    variant_id: int
    personalization: dict[str, Any] = Field(default_factory=dict)


_slug_re = re.compile(r"[^a-z0-9_]+")


def _slugify_model_name(s: str) -> str:
    """
    'iPhone 14 Pro' -> 'iphone_14_pro'
    """
    s = (s or "").strip().lower().replace(" ", "_")
    s = _slug_re.sub("", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _slugify_brand(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace(" ", "")
    s = _slug_re.sub("", s)
    return s


def _build_payload_from_personalization(design_key: str, p: dict[str, Any]) -> dict[str, str]:
    """
    Минимально: вытаскиваем значения по ключам.
    Ты можешь расширить позже.
    """
    def g(*keys: str) -> str:
        for k in keys:
            v = p.get(k)
            if v is None:
                continue
            v = str(v).strip()
            if v:
                return v
        return ""

    if design_key == "black-on-black-initials":
        raw = g("initials", "letters", "text")
        raw = raw.replace(" ", "").replace(".", "").replace("·", "").upper()
        if len(raw) < 2:
            return {}
        return {"line1": raw[0], "line2": raw[1]}

    if design_key == "black-on-black-initials-dot":
        raw = g("initials", "letters", "text").upper().replace(" ", "")
        raw = raw.replace("·", ".")
        if len(raw) == 2 and raw.isalpha():
            return {"initials": f"{raw[0]} · {raw[1]}"}
        return {"initials": raw.replace(".", " · ")}

    if design_key == "coords_top":
        c1 = g("coord_line1", "lat", "coord1")
        c2 = g("coord_line2", "lng", "coord2")
        if c1 and c2:
            return {"coord_line1": c1, "coord_line2": c2}
        coords = g("coords", "coord", "location")
        if "," in coords:
            a, b = coords.split(",", 1)
            return {"coord_line1": a.strip(), "coord_line2": b.strip()}
        return {"coord_line1": coords, "coord_line2": ""} if coords else {}

    if design_key == "date_top":
        raw = g("date", "day").replace(".", " · ").replace("·", " ")
        raw = " · ".join([x for x in raw.split() if x])
        return {"date": raw} if raw else {}

    if design_key == "number_bottom":
        raw = g("number", "plate", "car_number").upper()
        return {"number": raw} if raw else {}

    if design_key == "one-word":
        raw = g("word", "text", "name").upper()
        return {"word": raw} if raw else {}

    # fallback: если вдруг добавишь новые дизайны
    return {k: str(v) for k, v in p.items() if v is not None and str(v).strip()}


@router.post("/preview")
async def preview(req: MockupPreviewRequest, session: AsyncSession = Depends(get_async_session)):
    # 1) product -> design_key = product.slug
    product = (await session.execute(select(Product).where(Product.slug == req.product_slug))).scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Product not found")

    design_key = product.slug
    design = DESIGNS.get(design_key)
    if not design:
        raise HTTPException(400, f"Design config not found for slug '{design_key}'")

    # 2) variant
    v = (await session.execute(select(Variant).where(Variant.id == req.variant_id))).scalar_one_or_none()
    if not v:
        raise HTTPException(404, "Variant not found")

    brand = _slugify_brand(v.device_brand)
    model_slug = _slugify_model_name(v.device_model)

    # 3) mock path: lowercase + underscores + .webp
    base_path = MOCKS_DIR / brand / f"{model_slug}.webp"
    if not base_path.exists():
        raise HTTPException(404, f"Mock base not found: {base_path}")

    # 4) model layout key
    model_key = f"{brand}/{model_slug}"
    model_layout = MODEL_LAYOUTS.get(model_key)
    if not model_layout:
        raise HTTPException(400, f"Model layout not found for '{model_key}'")

    # 5) payload
    payload = _build_payload_from_personalization(design_key, req.personalization)
    if not any((val or "").strip() for val in payload.values()):
        raise HTTPException(400, "Empty personalization")

    # 6) render cached (CPU-bound -> thread)
    out_path = await run_in_threadpool(
        render_cached,
        CACHE_DIR,
        base_path,
        FONTS_DIR,
        model_layout,
        design,
        payload,
    )

    out_path = Path(out_path)
    rel = out_path.relative_to(CACHE_DIR).as_posix()
    public_url = f"/static/out/mockups/{rel}"

    return FileResponse(
        out_path,
        media_type="image/webp",
        headers={"X-Preview-Url": public_url},
    )