"""
One-time fix: backfill merchant mappings from existing FeedbackLogs.
These were previously lost because the merchant key extraction was incomplete
and commit() was never called.

Run: python fix_existing_corrections.py
"""
import asyncio
import sys
import re
sys.path.insert(0, '.')

_SMS_BRAND_KEYWORDS = [
    "netflix", "spotify", "hotstar", "prime", "zee5", "sonyliv", "sony liv",
    "amazon prime", "disney", "swiggy", "zomato", "uber", "ola", "rapido",
    "blinkit", "zepto", "bigbasket", "jio", "airtel", "bsnl", "vodafone",
    "bookmyshow", "inox", "pvr", "dream11", "mpl", "lenskart",
    "nykaa", "myntra", "flipkart", "amazon", "meesho", "ajio", "croma",
    "apollo", "medplus", "1mg", "pharmeasy", "netmeds",
    "lic", "hdfc life", "star health", "bajaj allianz",
    "irctc", "indigo", "spicejet",
    "dmart", "reliance", "bpcl", "hpcl", "indian oil",
]


def extract_key(tx):
    """Extract merchant key using all methods."""
    # Priority 1: merchant name
    if tx.merchant and tx.merchant.lower().strip() not in ("unknown", "", "none", "n/a"):
        return tx.merchant.lower().strip()

    # Priority 2: VPA prefix
    if tx.vpa:
        prefix = tx.vpa.split("@")[0].lower().strip()
        if prefix and not prefix.isdigit() and len(prefix) >= 2:
            return prefix

    # Priority 3: Known brands in SMS
    if tx.raw_sms:
        text = tx.raw_sms.lower()
        for brand in _SMS_BRAND_KEYWORDS:
            if brand in text:
                return brand.replace(" ", "_")

        # Priority 4: Generic SMS pattern
        patterns = [
            r"(?:debited for|deducted for|paid for|for)\s+([a-z0-9]+)",
            r"(?:subscription|purchase|payment)\s+(?:of\s+)?([a-z0-9]{3,20})",
            r"vpa\s+([a-z0-9.\-_]+)@",
            r"paid to\s+([a-z0-9\s&.\-]{3,25}?)(?:\s+via|\s+on|\.)",
            r"to\s+([a-z0-9\s&.\-]{3,25}?)(?:\s+via|\s+ref|\s+on)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                key = m.group(1).strip()
                if key and len(key) >= 3 and key not in ("the", "your", "this", "bank", "upi", "ref", "via"):
                    return key

    return None


async def run():
    from app.utils.db import AsyncSessionLocal
    from app.models.transaction import Transaction
    from app.models.learning import FeedbackLog, MerchantMapping
    from sqlalchemy import select
    from datetime import datetime

    async with AsyncSessionLocal() as db:
        # Load all feedback logs
        r1 = await db.execute(select(FeedbackLog))
        logs = r1.scalars().all()
        print(f"Found {len(logs)} feedback logs")

        saved = 0
        skipped = 0
        no_key = 0

        for log in logs:
            tx = await db.get(Transaction, log.transaction_id)
            if not tx:
                print(f"  SKIP: tx {log.transaction_id} not found")
                skipped += 1
                continue

            key = extract_key(tx)
            if not key:
                print(f"  NO KEY: tx {log.transaction_id} | raw_sms: {(tx.raw_sms or '')[:60]}")
                no_key += 1
                continue

            # Check if mapping already exists
            stmt = select(MerchantMapping).where(
                MerchantMapping.user_id == log.user_id,
                MerchantMapping.merchant_key == key,
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.category = log.corrected_category
                existing.sub_category = "General"
                existing.usage_count += 1
                existing.updated_at = datetime.utcnow()
                print(f"  UPDATED: '{key}' → {log.corrected_category}")
            else:
                db.add(MerchantMapping(
                    user_id=log.user_id,
                    merchant_key=key,
                    category=log.corrected_category,
                    sub_category="General",
                    confidence_override=0.99,
                    usage_count=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ))
                print(f"  SAVED:   '{key}' → {log.corrected_category}")
                saved += 1

        await db.commit()
        print(f"\n✅ Backfill done: {saved} new, {skipped} skipped, {no_key} no-key")

        # Verify
        r2 = await db.execute(select(MerchantMapping))
        maps = r2.scalars().all()
        print(f"\n📊 Total merchant mappings in DB: {len(maps)}")
        for m in maps:
            print(f"   '{m.merchant_key}' → {m.category}")


asyncio.run(run())
