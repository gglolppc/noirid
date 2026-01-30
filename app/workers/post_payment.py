# app/workers/post_payment.py
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload

from app.core.directories import STATIC_DIR
from app.db.models import Order
from app.db.session import AsyncSessionLocal
from app.services.emails import send_success_payment_email, send_tracking_email
from app.services.order_previews import persist_preview_files

log = logging.getLogger("postpay")

# сколько заказов обработаем за один запуск воркера (раз в минуту — более чем)
BATCH = 25


def utcnow():
    return datetime.now(timezone.utc)


async def process_one(session) -> bool:
    """
    Берём 1 заказ под обработку (skip_locked), делаем:
    - persist мокапов (если need_post_process)
    - payment email (если не отправлен)
    - tracking email (если tracking есть и не отправлен)
    Возвращает True если что-то сделали, иначе False.
    """

    stmt = (
        select(Order)
        .where(
            Order.status == "paid",
            or_(
                Order.need_post_process.is_(True),
                Order.confirmation_email_sent_at.is_(None),
                and_(Order.tracking_number.is_not(None), Order.tracking_email_sent_at.is_(None)),
            ),
        )
        .options(selectinload(Order.items))
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    result = await session.execute(stmt)
    order = result.scalars().unique().first()
    if not order:
        return False

    did_something = False

    try:
        log.info("Processing order %s", order.id)

        # 1) persist мокапов — только если нужно
        if order.need_post_process:
            items_data = [{"id": str(it.id), "url": it.preview_url} for it in order.items]

            updated_paths = await asyncio.to_thread(
                persist_preview_files,
                order_id=str(order.id),
                items_data=items_data,
                static_dir=Path(STATIC_DIR),
            )

            if updated_paths:
                updates_map = {r["id"]: r["new_url"] for r in updated_paths}
                for it in order.items:
                    new_url = updates_map.get(str(it.id))
                    if new_url:
                        it.preview_url = new_url

            order.need_post_process = False

            # фиксируем файлы/урлы как “важную часть”
            await session.commit()
            await session.refresh(order)

            did_something = True

        # 2) payment email
        if order.confirmation_email_sent_at is None:
            try:
                await send_success_payment_email(
                    email=order.customer_email,
                    order_number=order.order_number,
                )
                order.confirmation_email_sent_at = utcnow()
                await session.commit()
                await session.refresh(order)

                did_something = True
            except Exception:
                # письмо не ушло — БД не трогаем, воркер попробует снова
                await session.rollback()
                log.exception("Payment email failed for order %s", order.id)

        # 3) tracking email
        if order.tracking_number and order.tracking_email_sent_at is None:
            try:
                await send_tracking_email(
                    email=order.customer_email,
                    order_number=order.order_number,
                    tracking_number=order.tracking_number,
                )
                order.tracking_email_sent_at = utcnow()
                await session.commit()
                await session.refresh(order)

                did_something = True
            except Exception:
                await session.rollback()
                log.exception("Tracking email failed for order %s", order.id)

        return did_something

    except Exception:
        await session.rollback()
        log.exception("Failed to process order %s", order.id)
        return False


async def process_batch() -> int:
    processed = 0

    async with AsyncSessionLocal() as session:
        # Пробуем обработать до BATCH заказов за один запуск.
        for _ in range(BATCH):
            did = await process_one(session)
            if not did:
                break
            processed += 1

    return processed


async def main():
    n = await process_batch()
    log.info("Processed %s orders (did_something)", n)


if __name__ == "__main__":
    asyncio.run(main())
