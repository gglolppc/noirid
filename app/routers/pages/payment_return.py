from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_async_session
from app.db.models.order import Order
from app.services.twocheckout import TwoCOService

router = APIRouter(prefix="/payment/2co", tags=["pages"])


@router.api_route("/return", methods=["GET", "POST"], include_in_schema=False)
async def two_co_return(request: Request):
    form = dict(await request.form())
    query = dict(request.query_params)
    data = {**query, **form}

    # what 2CO returns :contentReference[oaicite:7]{index=7}
    order_number = data.get("order_number")
    total = data.get("total")
    key = data.get("key")
    merchant_order_id = data.get("merchant_order_id")  # наш order_id
    credit_ok = data.get("credit_card_processed")  # 'Y' if approved

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

    # Мы тут НЕ ставим paid. Максимум — показываем "processing".
    # paid будет по INS.
    msg = "Payment received. Processing confirmation..."
    if not credit_ok or str(credit_ok).upper() != "Y":
        msg = "Payment not approved or canceled."
    if not ok:
        msg = "Return validation failed. If you were charged, we’ll still confirm via webhook."

    order_link = f'<a href="/order/{merchant_order_id}" style="color:#e5e5e5">Open order</a>' if merchant_order_id else ""
    html = f"""
    <html><body style="font-family:ui-sans-serif; background:#0a0a0a; color:#e5e5e5; padding:40px">
      <h1 style="margin:0 0 12px">NOIRID</h1>
      <p style="opacity:.85">{msg}</p>
      <p style="opacity:.7; font-size:14px">Order: <b>{merchant_order_id or "-"}</b></p>
      <p style="opacity:.7; font-size:14px">{order_link or "You can close this tab."}</p>
    </body></html>
    """
    return HTMLResponse(html)
