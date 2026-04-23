import asyncio
import sys
sys.path.insert(0, '.')

async def check():
    from app.utils.db import AsyncSessionLocal
    from app.models.transaction import Transaction
    from app.models.learning import FeedbackLog, MerchantMapping
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        r1 = await db.execute(select(Transaction))
        txs = r1.scalars().all()
        print("=== TRANSACTIONS ===")
        print("Total:", len(txs))
        for tx in txs[:10]:
            print(f"  ID:{tx.id} | merchant:{tx.merchant} | vpa:{tx.vpa} | category:{tx.category} | confidence:{tx.confidence}")

        r2 = await db.execute(select(FeedbackLog))
        logs = r2.scalars().all()
        print("")
        print("=== FEEDBACK LOGS ===")
        print("Total:", len(logs))

        r3 = await db.execute(select(MerchantMapping))
        maps = r3.scalars().all()
        print("")
        print("=== MERCHANT MAPPINGS ===")
        print("Total:", len(maps))
        for m in maps:
            print(f"  {m.merchant_key} -> {m.category}")

asyncio.run(check())