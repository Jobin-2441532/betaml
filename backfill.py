import asyncio
import sys
sys.path.insert(0, '.')

async def run():
    from app.utils.db import AsyncSessionLocal
    from app.models.transaction import Transaction
    from app.models.learning import FeedbackLog, MerchantMapping
    from sqlalchemy import select
    from datetime import datetime

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(FeedbackLog))
        logs = result.scalars().all()
        print("Feedback logs found:", len(logs))

        saved = 0

        for log in logs:
            tx = await db.get(Transaction, log.transaction_id)
            if not tx:
                continue

            key = None

            if tx.merchant and tx.merchant.lower().strip() not in ('unknown','','none'):
                key = tx.merchant.lower().strip()
            elif tx.vpa:
                prefix = tx.vpa.split('@')[0].lower().strip()
                if not prefix.isdigit():
                    key = prefix

            if not key:
                continue

            r2 = await db.execute(select(MerchantMapping).where(
                MerchantMapping.user_id == log.user_id,
                MerchantMapping.merchant_key == key
            ))

            if not r2.scalar_one_or_none():
                db.add(MerchantMapping(
                    user_id=log.user_id,
                    merchant_key=key,
                    category=log.corrected_category,
                    sub_category='General',
                    confidence_override=0.99,
                    usage_count=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
                saved += 1
                print("Saved:", key, "->", log.corrected_category)

        await db.commit()
        print("Backfill complete. Saved:", saved)

asyncio.run(run())