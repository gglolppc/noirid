from sqlalchemy import text
from app.db.session import AsyncSessionLocal

ARCHIVE_SQL = """
UPDATE orders
SET status = 'archived'
WHERE
    (status = 'draft' AND created_at < NOW() - INTERVAL '24 hours')
 OR (status = 'pending_payment' AND created_at < NOW() - INTERVAL '36 hours')
RETURNING id;
"""

async def archive_old_orders() -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(ARCHIVE_SQL))
        archived_ids = result.scalars().all()
        await session.commit()
        return len(archived_ids)