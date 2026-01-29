# app/workers/post_payment.py
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.db.models import Order
from app.core.directories import STATIC_DIR
from app.services.order_previews import persist_preview_files
from app.services.emails import send_success_payment_email

log = logging.getLogger("postpay")

BATCH = 10

async def process_batch() -> int:
    processed = 0
    async with AsyncSessionLocal() as session:
        while True:
            stmt = (
                select(Order)
                .where(Order.status == "paid", Order.need_post_process.is_(True))
                .options(selectinload(Order.items))
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            result = await session.execute(stmt)
            order = result.scalars().unique().first()
            if not order:
                break

            try:
                log.info("Processing order %s", order.id)

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
                await session.commit()  # фиксируем всё важное

                # processed считаем здесь — заказ обработан успешно
                processed += 1

                # Reload, чтобы быть уверенным в актуальном sent_at
                await session.refresh(order)

                if order.confirmation_email_sent_at is None:
                    try:
                        await send_success_payment_email(
                            email=order.customer_email,
                            order_number=order.order_number,
                        )
                        async with AsyncSessionLocal() as email_session:
                            db_order = await email_session.get(Order, order.id)
                            if db_order and db_order.confirmation_email_sent_at is None:
                                db_order.confirmation_email_sent_at = datetime.now(timezone.utc)
                                await email_session.commit()
                    except Exception:
                        log.exception("Email failed for order %s", order.id)
                        # Заказ всё равно обработан

            except Exception:
                await session.rollback()
                log.exception("Failed to process order %s", order.id)
                # continue — следующий заказ

    return processed

async def main():
    n = await process_batch()
    log.info("Processed %s orders", n)

if __name__ == "__main__":
    asyncio.run(main())