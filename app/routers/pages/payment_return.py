from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_async_session
from app.db.models.order import Order
from app.services.twocheckout import TwoCOService
from app.core.templates import templates

router = APIRouter(prefix="/payment/2co", tags=["pages"])


from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates


@router.api_route("/return", methods=["GET", "POST"], include_in_schema=False)
async def two_co_return(request: Request):
    form = dict(await request.form())
    query = dict(request.query_params)
    data = {**query, **form}

    order_number = data.get("order_number")
    total = data.get("total")
    key = data.get("key")
    merchant_order_id = data.get("merchant_order_id")
    credit_ok = data.get("credit_card_processed")

    sid = os.getenv("TCO_MERCHANT_CODE", "")
    secret_word = os.getenv("TCO_SECRET_WORD", "")
    demo = os.getenv("TCO_DEMO", "1") == "1"

    ok = False
    if sid and secret_word and order_number and total and key:
        ok = TwoCOService.verify_return_md5(
            secret_word=secret_word,
            sid=sid,
            order_number=str(order_number),
            total=str(total),
            received_key=str(key),
            is_demo=demo,
        )

    msg = "Payment received. Processing confirmation..."
    if not credit_ok or str(credit_ok).upper() != "Y":
        msg = "Payment not approved or canceled."
    if not ok:
        msg = "Return validation failed."

    # Возвращаем через шаблонизатор
    return templates.TemplateResponse(
        "pages/payment_status.html",
        {
            "request": request,
            "msg": msg,
            "merchant_order_id": merchant_order_id
        }
    )