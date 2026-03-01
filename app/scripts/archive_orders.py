import asyncio
from app.workers.archive_orders import archive_old_orders

async def main():
    count = await archive_old_orders()
    print(f"Archived {count} orders")

if __name__ == "__main__":
    asyncio.run(main())