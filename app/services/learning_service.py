"""app/services/learning_service.py - Learning from user corrections."""

from __future__ import annotations
from datetime import datetime
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import FeedbackLog, MerchantMapping
from app.models.transaction import Transaction


def _extract_merchant_key(tx: Transaction) -> str | None:
    """Extract best possible merchant key from a transaction."""

    # Priority 1: merchant name
    if tx.merchant and tx.merchant.lower().strip() not in (
        "unknown", "", "none", "n/a"
    ):
        return tx.merchant.lower().strip()

    # Priority 2: VPA prefix
    if tx.vpa:
        prefix = tx.vpa.split("@")[0].lower().strip()
        if prefix and not prefix.isdigit():
            return prefix

    # Priority 3: Extract from raw SMS (INCLUDING P2P)
    if tx.raw_sms:
        text = tx.raw_sms.lower()

        patterns = [
            r"vpa\s+([a-z0-9.\-_]+)@",
            r"paid to\s+([a-z0-9\s&.\-]{3,25}?)(?:\s+via|\s+on|\.)",
            r"to\s+([a-z0-9\s&.\-]{3,25}?)(?:\s+via|\s+ref|\s+on)",

            # 🔥 P2P FIX (MOST IMPORTANT)
            r"from\s+([a-z\s]{2,20})",
        ]

        for pat in patterns:
            m = re.search(pat, text)
            if m:
                key = m.group(1).strip()

                # 🚫 filter garbage values
                if key in (
                    "the", "your", "upi", "account",
                    "bank", "ref", "transfer"
                ):
                    continue

                if len(key) > 2:
                    return key

    return None


class LearningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_correction(
        self,
        user_id: int,
        transaction_id: int,
        corrected_category: str,
        corrected_sub_category: str,
    ) -> None:

        tx = await self.db.get(Transaction, transaction_id)
        if not tx or tx.user_id != user_id:
            return

        original_category = tx.category or "Uncategorised"

        # 1️⃣ Log feedback
        log = FeedbackLog(
            user_id=user_id,
            transaction_id=transaction_id,
            original_category=original_category,
            corrected_category=corrected_category,
            original_confidence=tx.confidence or 0.0,
            created_at=datetime.utcnow(),
        )
        self.db.add(log)

        # 2️⃣ Extract merchant key (NOW SUPPORTS P2P)
        merchant_key = _extract_merchant_key(tx)

        if merchant_key:
            await self._upsert_mapping(
                user_id,
                merchant_key,
                corrected_category,
                corrected_sub_category,
            )

            # Also store VPA prefix if available
            if tx.vpa:
                vpa_prefix = tx.vpa.split("@")[0].lower().strip()
                if (
                    vpa_prefix
                    and vpa_prefix != merchant_key
                    and not vpa_prefix.isdigit()
                ):
                    await self._upsert_mapping(
                        user_id,
                        vpa_prefix,
                        corrected_category,
                        corrected_sub_category,
                    )
        else:
            print(f"⚠️ No merchant key found for tx {transaction_id}")

        # 3️⃣ Update transaction
        tx.category = corrected_category
        tx.sub_category = corrected_sub_category
        tx.confidence = 0.99

        await self.db.flush()

    async def get_merchant_mappings(self, user_id: int) -> dict:
        stmt = select(MerchantMapping).where(
            MerchantMapping.user_id == user_id
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        return {
            r.merchant_key: (r.category, r.sub_category)
            for r in rows
        }

    async def get_feedback_stats(self, user_id: int) -> dict:
        stmt = select(FeedbackLog).where(
            FeedbackLog.user_id == user_id
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        from collections import Counter
        counter = Counter(l.original_category for l in logs)

        return {
            "total_corrections": len(logs),
            "most_corrected_categories": counter.most_common(5),
        }

    async def _upsert_mapping(
        self,
        user_id: int,
        merchant_key: str,
        category: str,
        sub_category: str,
    ) -> None:

        key = merchant_key.lower().strip()

        if not key or len(key) < 2:
            return

        stmt = select(MerchantMapping).where(
            MerchantMapping.user_id == user_id,
            MerchantMapping.merchant_key == key,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # ✅ UPDATE (no duplicates anymore)
            existing.category = category
            existing.sub_category = sub_category
            existing.usage_count += 1
            existing.updated_at = datetime.utcnow()
        else:
            self.db.add(MerchantMapping(
                user_id=user_id,
                merchant_key=key,
                category=category,
                sub_category=sub_category,
                confidence_override=0.99,
                usage_count=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))