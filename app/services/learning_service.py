"""app/services/learning_service.py - Learning from user corrections."""

from __future__ import annotations
from datetime import datetime
import re
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import FeedbackLog, MerchantMapping
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


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


# Known brand keywords to extract from raw SMS when no merchant/VPA exists
_SMS_BRAND_KEYWORDS = [
    "netflix", "spotify", "hotstar", "prime", "zee5", "sonyliv", "sony liv",
    "amazon prime", "disney", "swiggy", "zomato", "uber", "ola", "rapido",
    "blinkit", "zepto", "bigbasket", "jio", "airtel", "bsnl", "vodafone",
    "bookmyshow", "inox", "pvr", "dream11", "mpl", "cult.fit", "lenskart",
    "nykaa", "myntra", "flipkart", "amazon", "meesho", "ajio", "croma",
    "apollo", "medplus", "1mg", "pharmeasy", "netmeds",
    "lic", "hdfc life", "star health", "bajaj allianz",
    "irctc", "indigo", "spicejet", "goair",
    "dmart", "reliance", "bpcl", "hpcl", "indian oil",
]


def _extract_keyword_from_sms(raw_sms: str | None) -> str | None:
    """
    For bank SMS that have no merchant/VPA (e.g. 'Rs.499 debited for NETFLIX subscription'),
    extract a known brand keyword to use as a merchant mapping key.
    """
    if not raw_sms:
        return None

    text = raw_sms.lower()

    # Try matching against known brands first
    for brand in _SMS_BRAND_KEYWORDS:
        if brand in text:
            # Return sanitized brand name as key (remove spaces for storage)
            return brand.replace(" ", "_")

    # Generic pattern: look for 'for <WORD>' or 'to <WORD>' in bank SMS
    patterns = [
        r"(?:debited for|deducted for|paid for|for)\s+([a-z0-9]+)",
        r"(?:subscription|purchase|payment)\s+(?:of\s+)?([a-z0-9]{3,20})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            key = m.group(1).strip()
            if key and len(key) >= 3 and key not in (
                "the", "your", "this", "bank", "upi", "ref", "via"
            ):
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
            logger.warning(f"record_correction: tx {transaction_id} not found or wrong user")
            return

        # Ensure sub_category is never empty (prevent NOT NULL constraint failure)
        corrected_sub_category = corrected_sub_category or "General"

        original_category = tx.category or "Uncategorised"

        try:
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

            # 2️⃣ Extract merchant key
            merchant_key = _extract_merchant_key(tx)
            
            from app.utils.patterns import is_p2p_vpa
            is_p2p = bool(tx.vpa and is_p2p_vpa(tx.vpa)) or bool(tx.tags and "p2p" in tx.tags.split(","))

            if merchant_key and not is_p2p:
                await self._upsert_mapping(
                    user_id,
                    merchant_key,
                    corrected_category,
                    corrected_sub_category,
                )

                # Also store VPA prefix if available and different from merchant key
                if tx.vpa:
                    vpa_prefix = tx.vpa.split("@")[0].lower().strip()
                    if (
                        vpa_prefix
                        and vpa_prefix != merchant_key
                        and not vpa_prefix.isdigit()
                        and len(vpa_prefix) >= 2
                    ):
                        await self._upsert_mapping(
                            user_id,
                            vpa_prefix,
                            corrected_category,
                            corrected_sub_category,
                        )
            elif not is_p2p:
                # No merchant key from name/vpa — store raw SMS keyword as key
                # This handles bank SMS like NETFLIX, SPOTIFY etc.
                sms_key = _extract_keyword_from_sms(tx.raw_sms)
                if sms_key:
                    await self._upsert_mapping(
                        user_id,
                        sms_key,
                        corrected_category,
                        corrected_sub_category,
                    )
                    logger.info(f"Stored SMS keyword key '{sms_key}' for tx {transaction_id}")
                else:
                    logger.warning(f"⚠️ No merchant key found for tx {transaction_id} — raw_sms: {(tx.raw_sms or '')[:80]}")

            # 3️⃣ Update transaction category
            tx.category = corrected_category
            tx.sub_category = corrected_sub_category
            tx.confidence = 0.99

            await self.db.flush()
            # ✅ CRITICAL FIX: Explicitly commit so merchant mappings are persisted
            await self.db.commit()
            logger.info(f"✅ Correction saved: tx {transaction_id} → {corrected_category} (merchant key saved)")

        except Exception as e:
            logger.error(f"❌ record_correction failed for tx {transaction_id}: {e}")
            await self.db.rollback()
            raise

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

        # Ensure sub_category is never empty
        sub_category = sub_category or "General"

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
            logger.info(f"  Updated mapping: '{key}' → {category}")
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
            logger.info(f"  New mapping: '{key}' → {category}")