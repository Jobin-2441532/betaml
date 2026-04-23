import asyncio
import sys
sys.path.insert(0, '.')

async def fix():
    from app.utils.db import AsyncSessionLocal
    from app.models.transaction import Transaction
    from app.models.learning import MerchantMapping, FeedbackLog
    from sqlalchemy import select
    from datetime import datetime
    import re

    def extract_merchant_key(tx):
        """Smart extraction including P2P like 'from Mom'"""

        # 1. Merchant
        if tx.merchant and tx.merchant.lower().strip() not in ("unknown", "", "none"):
            return tx.merchant.lower().strip()

        # 2. VPA prefix
        if tx.vpa:
            prefix = tx.vpa.split("@")[0].lower().strip()
            if prefix and not prefix.isdigit():
                return prefix

        # 3. Extract from SMS (P2P FIX 🔥)
        if tx.raw_sms:
            text = tx.raw_sms.lower()

            patterns = [
                r"from\s+([a-z\s]{2,20})",  # 🔥 MOST IMPORTANT
                r"paid to\s+([a-z0-9\s&.\-]{3,25})",
                r"to\s+([a-z0-9\s&.\-]{3,25})",
            ]

            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    key = m.group(1).strip()

                    # filter garbage
                    if key in ("the", "your", "upi", "account", "bank", "ref"):
                        continue

                    if len(key) > 2:
                        return key

        return None

    async with AsyncSessionLocal() as db:

        # ✅ FIX 1 — Use ALL corrected transactions
        r1 = await db.execute(
            select(Transaction).where(
                Transaction.user_id == 1,
                Transaction.confidence >= 0.99
            )
        )
        txs = r1.scalars().all()
        print(f"Found {len(txs)} corrected transactions")

        saved = 0

        for tx in txs:
            if not tx.category or tx.category in ("Uncategorised", "Needs Review"):
                continue

            key = extract_merchant_key(tx)

            if not key:
                print(f"⚠️ Skipped tx {tx.id} (no key)")
                continue

            key = key.lower().strip()

            # ✅ FIX 2 — UPSERT instead of duplicate insert
            r2 = await db.execute(
                select(MerchantMapping).where(
                    MerchantMapping.user_id == 1,
                    MerchantMapping.merchant_key == key,
                )
            )
            existing = r2.scalar_one_or_none()

            if existing:
                existing.category = tx.category
                existing.sub_category = tx.sub_category or "General"
                existing.usage_count += 1
                existing.updated_at = datetime.utcnow()
            else:
                db.add(MerchantMapping(
                    user_id=1,
                    merchant_key=key,
                    category=tx.category,
                    sub_category=tx.sub_category or "General",
                    confidence_override=0.99,
                    usage_count=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ))
                saved += 1
                print(f"  Saved: [{key}] -> {tx.category}")

            # ✅ Ensure feedback log exists
            r4 = await db.execute(
                select(FeedbackLog).where(
                    FeedbackLog.transaction_id == tx.id
                )
            )
            existing_log = r4.scalar_one_or_none()

            if not existing_log:
                db.add(FeedbackLog(
                    user_id=1,
                    transaction_id=tx.id,
                    original_category="Uncategorised",
                    corrected_category=tx.category,
                    original_confidence=0.0,
                    created_at=datetime.utcnow(),
                ))

        await db.commit()

        print(f"\n✅ Done! Created {saved} new mappings")

        # 🔍 Verify
        r3 = await db.execute(select(MerchantMapping))
        maps = r3.scalars().all()

        print(f"\nTotal mappings now: {len(maps)}")
        for m in maps:
            print(f"  {m.merchant_key} -> {m.category}")

        r5 = await db.execute(select(FeedbackLog))
        logs = r5.scalars().all()
        print(f"\nTotal feedback logs: {len(logs)}")

asyncio.run(fix())