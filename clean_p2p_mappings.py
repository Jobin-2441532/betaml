import asyncio
import sys
sys.path.insert(0, '.')

async def clean_db():
    from app.utils.db import AsyncSessionLocal
    from app.models.learning import MerchantMapping
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(MerchantMapping))
        maps = r.scalars().all()
        count = 0
        for m in maps:
            if "via upi" in m.merchant_key.lower():
                print(f"Deleting bad P2P mapping: {m.merchant_key}")
                await db.delete(m)
                count += 1
        
        await db.commit()
        print(f"Deleted {count} bad mappings.")

asyncio.run(clean_db())
