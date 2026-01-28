from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[2]  # .../noirid
STATIC_DIR = BASE_DIR / "app" / "static"