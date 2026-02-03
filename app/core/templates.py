from __future__ import annotations
from fastapi import Request
from pathlib import Path
from datetime import datetime
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[2]  # .../noirid
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def inject_common_vars(request: Request):
    return {
        "current_year": datetime.now().year
    }

# Просто добавляем функцию в список процессоров
templates.context_processors.append(inject_common_vars)