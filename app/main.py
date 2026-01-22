from __future__ import annotations

import os

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.logger_setup import setup_logging

from app.routers.pages.home import router as home_router
from app.routers.pages.catalog import router as catalog_router
from app.routers.pages.product import router as product_router
from app.routers.pages.cart import router as cart_page_router
from app.routers.api.cart import router as cart_api_router
from app.routers.pages.checkout import router as checkout_page_router
from app.routers.api.checkout import router as checkout_api_router
from app.routers.api.payments_2co import router as payments_2co_router
from app.routers.pages.payment_return import router as payment_return_router
from app.routers.webhooks.twocheckout_ins import router as twocheckout_ins_router
from app.routers.api.orders import router as orders_api_router
from app.routers.pages.order_status import router as order_status_page_router
from app.routers.pages.admin import router as admin_router



setup_logging(settings.env)

app = FastAPI(title=settings.app_name)

script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, "static/")

app.mount("/static", StaticFiles(directory=st_abs_file_path), name="static")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    same_site="lax",
    https_only=(settings.env != "dev"),
)

app.include_router(home_router)
app.include_router(catalog_router)
app.include_router(product_router)
app.include_router(cart_page_router)
app.include_router(cart_api_router)
app.include_router(checkout_page_router)
app.include_router(checkout_api_router)
app.include_router(payments_2co_router)
app.include_router(payment_return_router)
app.include_router(twocheckout_ins_router)
app.include_router(orders_api_router)
app.include_router(order_status_page_router)
app.include_router(admin_router)

@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
