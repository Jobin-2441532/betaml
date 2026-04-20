from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.learning import FeedbackLog, MerchantMapping
from app.models.transaction import Transaction

class LearningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_correction(self, user_id, transaction_id, corrected_category, corrected_sub_category):
        tx = await self.db.get(Transaction, transaction_id)
        if not tx or tx.user_id != user_id: return

        log = FeedbackLog(
            user_id=user_id, transaction_id=transaction_id,
            original_category=tx.category or "Uncategorised",
            corrected_category=corrected_category,
            original_confidence=tx.confidence or 0.0,
        )
        self.db.add(log)

        if tx.merchant:
            await self._upsert_mapping(user_id, tx.merchant, corrected_category, corrected_sub_category)

        tx.category = corrected_category
        tx.sub_category = corrected_sub_category
        tx.confidence = 0.99
        await self.db.flush()

    async def get_merchant_mappings(self, user_id: int) -> dict:
        stmt = select(MerchantMapping).where(MerchantMapping.user_id == user_id)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return {r.merchant_key: (r.category, r.sub_category) for r in rows}

    async def get_feedback_stats(self, user_id: int) -> dict:
        stmt = select(FeedbackLog).where(FeedbackLog.user_id == user_id)
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        from collections import Counter
        counter = Counter(l.original_category for l in logs)
        return {"total_corrections": len(logs), "most_corrected": counter.most_common(5)}

    async def _upsert_mapping(self, user_id, merchant, category, sub_category):
        key = merchant.lower().strip()
        stmt = select(MerchantMapping).where(
            MerchantMapping.user_id == user_id,
            MerchantMapping.merchant_key == key,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.category = category
            existing.sub_category = sub_category
            existing.usage_count += 1
            existing.updated_at = datetime.utcnow()
        else:
            self.db.add(MerchantMapping(
                user_id=user_id, merchant_key=key,
                category=category, sub_category=sub_category,
                confidence_override=0.99, usage_count=1,
            ))