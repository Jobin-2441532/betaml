import asyncio
import sys
sys.path.insert(0, '.')

async def clear():
    from app.utils.db import AsyncSessionLocal
    from app.models.learning import MerchantMapping
    from sqlalchemy import delete

    async with AsyncSessionLocal() as db:
        result = await db.execute(delete(MerchantMapping))
        await db.commit()
        print("✅ All merchant mappings deleted")

asyncio.run(clear())