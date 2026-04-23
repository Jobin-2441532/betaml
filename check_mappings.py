import asyncio
from app.utils.db import AsyncSessionLocal
from app.models.learning import MerchantMapping
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MerchantMapping))
        rows = result.scalars().all()
        print("Total merchant mappings:", len(rows))

asyncio.run(run())