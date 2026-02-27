from __future__ import annotations
import os
import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_session
from app.repos.checkout import CheckoutRepo
from app.db.models.payment import Payment
from app.repos.payments import PaymentRepo

router = APIRouter(prefix="/api/payments/paypal", tags=["payments"])
log = logging.getLogger("payments")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")


async def get_paypal_token():
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
        )
        res.raise_for_status()
        return res.json()["access_token"]


@router.post("/create")
async def create_order(request: Request, session: AsyncSession = Depends(get_async_session)):
    try:
        order_id = request.session.get("order_id")
        if not order_id:
            raise HTTPException(status_code=400, detail="No order in session")

        order = await CheckoutRepo.get_order_any(session, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # 1. Создаем запись о платеже
        payment = Payment(
            order_id=order.id,
            provider="paypal",
            status="created",
            amount=order.total,
            currency="EUR",
        )
        # Добавляем в сессию
        session.add(payment)
        # Делаем flush, чтобы получить ID платежа, если нужно, но пока просто идем дальше

        addr = order.shipping_address or {}
        country_code = addr.get("country", "MD").upper()

        token = await get_paypal_token()

        async with httpx.AsyncClient() as client:
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": str(order.id),
                    "amount": {
                        "currency_code": "EUR",
                        "value": f"{order.total:.2f}"
                    },
                    "shipping": {
                        "name": {"full_name": order.customer_name},
                        "address": {
                            "address_line_1": addr.get("line1", ""),
                            "admin_area_2": addr.get("city", ""),
                            "postal_code": addr.get("postal_code", ""),
                            "country_code": country_code
                        }
                    }
                }],
                "application_context": {
                    "shipping_preference": "SET_PROVIDED_ADDRESS",
                    "user_action": "PAY_NOW",
                    "brand_name": "NOIRID"
                }
            }

            res = await client.post(
                f"{PAYPAL_BASE_URL}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )

            if res.status_code != 201:
                log.error(f"PayPal API Rejected: {res.text}")
                raise HTTPException(status_code=400, detail="PayPal setup failed")

            paypal_data = res.json()

            # 2. ВАЖНО: Привязываем ID заказа PayPal к нашему платежу и сохраняем
            payment.provider_order_number = paypal_data.get("id")
            await session.commit()  # ТЕПЕРЬ ОНО ТОЧНО В БАЗЕ

            return paypal_data

    except Exception as e:
        log.exception("PayPal create error")
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/{paypal_order_id}")
async def capture_order(
        paypal_order_id: str,
        request: Request,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        token = await get_paypal_token()
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{PAYPAL_BASE_URL}/v2/checkout/orders/{paypal_order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={}
            )

            data = res.json()

            if res.status_code == 201 and data.get("status") == "COMPLETED":
                purchase_unit = data.get("purchase_units", [{}])[0]
                internal_uuid = purchase_unit.get("reference_id")
                capture_id = purchase_unit.get("payments", {}).get("captures", [{}])[0].get("id")

                order = await CheckoutRepo.get_order_any(session, internal_uuid)
                if not order:
                    raise HTTPException(status_code=404, detail="Order not found")

                # Ищем наш платеж по provider_order_number (это paypal_order_id)
                from sqlalchemy import select
                q = select(Payment).where(Payment.provider_order_number == paypal_order_id)
                payment_exec = await session.execute(q)
                payment = payment_exec.scalars().first()

                # Обновляем заказ
                order.payment_status = "paid"
                order.status = "paid"
                order.paypal_capture_id = capture_id
                order.need_post_process = True

                # Обновляем платеж
                if payment:
                    payment.status = "paid"
                    payment.provider_invoice_id = capture_id
                    payment.raw_payload = data
                else:
                    log.warning(f"Payment record not found for PayPal ID {paypal_order_id}")

                await session.commit()
                request.session.pop("order_id", None)

                log.info(f"Order {order.order_number} PAID")
                return {"status": "success", "order_number": order.order_number}

            log.error(f"PayPal Capture Error: {data}")
            return {"status": "error", "detail": "Payment failed"}

    except Exception as e:
        log.exception("PayPal capture exception")
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))