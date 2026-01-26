from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from pydantic import BaseModel, Field, field_validator

# -----------------------------
# Config models (Pydantic v2)
# -----------------------------

Align = Literal["left", "center", "right"]
Style = Literal["deboss", "emboss", "flat"]
TextTransform = Literal["none", "upper", "lower"]

AnchorName = Literal[
    "center",
    "bottom",
    "top",
    "bottom_text",
    "top_text",
    "custom",
]


class Anchor(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class ModelLayout(BaseModel):
    anchors: dict[str, Anchor]
    safe_x0: float = Field(default=0.0, ge=0.0, le=1.0)
    safe_y0: float = Field(default=0.0, ge=0.0, le=1.0)
    safe_x1: float = Field(default=1.0, ge=0.0, le=1.0)
    safe_y1: float = Field(default=1.0, ge=0.0, le=1.0)


class TextSlot(BaseModel):
    key: str
    anchor: str = "center"
    dx: float = 0.0
    dy: float = 0.0
    font: str = "NOIRID_Custom.ttf"
    font_px: int = Field(ge=1)
    tracking: int = 0
    align: Align = "center"
    max_width: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    min_font_px: int = 10
    transform: TextTransform = "upper"
    stroke_width: int = 0
    blur_after: float = 0.8

    @field_validator("min_font_px")
    @classmethod
    def _min_le_font(cls, v, info):
        font_px = info.data.get("font_px", 1)
        return min(v, font_px)


class DesignTemplate(BaseModel):
    name: str
    style: Style = "deboss"
    slots: list[TextSlot]
    highlight_alpha: float = 0.10
    shadow_alpha: float = 0.32
    press_alpha: float = 0.10
    ink_alpha: float = 0.60


# -----------------------------
# Helpers (Optimized)
# -----------------------------

@lru_cache(maxsize=32)
def _get_font(font_path: str, size: int):
    return ImageFont.truetype(font_path, size)


def _apply_transform(s: str, t: TextTransform) -> str:
    s = (s or "").strip()
    if t == "upper": return s.upper()
    if t == "lower": return s.lower()
    return s


def _measure_tracked(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, tracking: int) -> int:
    if not text: return 0
    w = int(draw.textlength(text, font=font))
    if tracking != 0:
        w += tracking * (len(text) - 1)
    return w


def _draw_tracked_text(
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        tracking: int,
        fill: int,
        stroke_width: int = 0,
):
    cur_x = x
    for i, ch in enumerate(text):
        draw.text(
            (cur_x, y), ch, font=font, fill=fill,
            stroke_width=stroke_width, stroke_fill=fill
        )
        cur_x += int(draw.textlength(ch, font=font)) + tracking


def _fit_font_to_width(
        draw: ImageDraw.ImageDraw,
        text: str,
        font_path: Path,
        start_px: int,
        min_px: int,
        tracking: int,
        max_w_px: int,
) -> ImageFont.FreeTypeFont:
    lo, hi = min_px, start_px
    best = lo
    f_str = str(font_path)

    while lo <= hi:
        mid = (lo + hi) // 2
        f = _get_font(f_str, mid)
        if _measure_tracked(draw, text, f, tracking) <= max_w_px:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return _get_font(f_str, best)


def _cache_key(base_path: str, layout: ModelLayout, design: DesignTemplate, payload: dict, fonts_dir: str) -> str:
    raw = f"{base_path}|{layout.model_dump()}|{design.model_dump()}|{payload}|{fonts_dir}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# -----------------------------
# Main render (Optimized)
# -----------------------------

def render_mockup_from_config(
        base_image_path: Path,
        fonts_dir: Path,
        model_layout: ModelLayout,
        design: DesignTemplate,
        payload: dict[str, str],
        out_path: Path | None = None,
) -> Image.Image:
    # 1. Загрузка базы
    base = Image.open(base_image_path).convert("RGBA")
    W, H = base.size

    # 2. Создание маски
    mask = Image.new("L", (W, H), 0)
    dmask = ImageDraw.Draw(mask)

    for slot in design.slots:
        raw = payload.get(slot.key, "")
        text = _apply_transform(raw, slot.transform)
        if not text: continue

        anchor = model_layout.anchors.get(slot.anchor, Anchor(x=0.5, y=0.5))
        ax, ay = int(W * (anchor.x + slot.dx)), int(H * (anchor.y + slot.dy))

        font_path = fonts_dir / slot.font
        if slot.max_width is not None:
            font = _fit_font_to_width(dmask, text, font_path, slot.font_px, slot.min_font_px, slot.tracking,
                                      int(W * slot.max_width))
        else:
            font = _get_font(str(font_path), slot.font_px)

        text_w = _measure_tracked(dmask, text, font, slot.tracking)
        x0 = ax - text_w // 2 if slot.align == "center" else (ax - text_w if slot.align == "right" else ax)
        y0 = ay - (font.size // 2)

        _draw_tracked_text(dmask, x0, y0, text, font, slot.tracking, 255, slot.stroke_width)

    mask_soft = mask.filter(ImageFilter.GaussianBlur(0.6))

    # 3. Сборка эффектов в один слой (overlay)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    if design.style == "flat":
        ink_color = (0, 0, 0, int(255 * design.ink_alpha))
        ink_layer = Image.new("RGBA", (W, H), ink_color)
        overlay = Image.composite(ink_layer, overlay, mask_soft)
    else:
        # Emboss / Deboss
        off = 2 if design.style == "emboss" else 3

        # Shadow
        sh_m = ImageChops.offset(mask_soft, off, off).filter(ImageFilter.GaussianBlur(2.0))
        sh_layer = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * design.shadow_alpha)))
        overlay = Image.composite(sh_layer, overlay, sh_m)

        # Highlight
        hi_m = ImageChops.offset(mask_soft, -off, -off).filter(ImageFilter.GaussianBlur(1.5))
        hi_layer = Image.new("RGBA", (W, H), (255, 255, 255, int(255 * design.highlight_alpha)))
        overlay = Image.composite(hi_layer, overlay, hi_m)

        # Ink + Press (объединяем в один проход)
        fill_alpha = min(1.0, design.ink_alpha + design.press_alpha)
        fill_layer = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fill_alpha)))
        overlay = Image.composite(fill_layer, overlay, mask_soft)

    # 4. Один финальный композит
    out = Image.alpha_composite(base, overlay)

    if out_path:
        # method=0 - критично для скорости генерации превью
        out.save(out_path, "WEBP", quality=90, method=0)

    return out


def render_cached(
        cache_dir: Path,
        base_image_path: Path,
        fonts_dir: Path,
        model_layout: ModelLayout,
        design: DesignTemplate,
        payload: dict[str, str],
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    ck = _cache_key(str(base_image_path), model_layout, design, payload, str(fonts_dir))
    out_path = cache_dir / f"{ck}.webp"

    if not out_path.exists():
        render_mockup_from_config(
            base_image_path=base_image_path,
            fonts_dir=fonts_dir,
            model_layout=model_layout,
            design=design,
            payload=payload,
            out_path=out_path,
        )

    return out_path