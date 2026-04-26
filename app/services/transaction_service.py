from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.core.classifier import HybridClassifier
from app.core.confidence import ConfidenceAction, ConfidenceEngine
from app.core.sms_parser import SMSParser
from app.models.transaction import Transaction, TransactionType, ReviewStatus
from app.services.learning_service import LearningService
from app.models.learning import UserSalaryProfile
from app.models.split import WalletFloat
from app.utils.patterns import REFUND_KEYWORDS, RECURRING_KEYWORDS, match_keyword
from config.settings import settings   # ✅ FIXED: added missing import


class TransactionService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self._parser = SMSParser()
        self._confidence_engine = ConfidenceEngine()
        self._learning_service = LearningService(db)

    async def process_sms(
        self, sms_text: str, location_lat=None,
        location_lon=None, location_label=None
    ) -> dict:

        from app.utils.patterns import (
            is_mixed_basket_merchant, is_p2p_vpa,
            is_cashback_transaction, is_deposit_transaction,
            DEPOSIT_KEYWORDS, match_keyword
        )

        parsed = self._parser.parse(sms_text)

        if "OTP" in sms_text.upper():
            return {"error": "Ignored SMS containing OTP", "raw_sms": sms_text}

        if parsed.amount is None:
            return {"error": "Could not parse amount from SMS", "raw_sms": sms_text}

        merchant_mappings = await self._learning_service.get_merchant_mappings(self.user_id)
        classifier = HybridClassifier(merchant_mappings=merchant_mappings)
        clf = classifier.classify(parsed)

        is_known_merchant = bool(
            parsed.merchant and parsed.merchant.lower().strip() in merchant_mappings
        ) or bool(
            # Also check VPA prefix
            parsed.vpa and parsed.vpa.split("@")[0].lower().strip() in merchant_mappings
        ) or bool(
            # Also check raw SMS text for stored keys (handles bank SMS like Netflix)
            merchant_mappings and parsed.raw_text and any(
                len(k) >= 3 and k in parsed.raw_text.lower()
                for k in merchant_mappings
            )
        )

        score = self._confidence_engine.score(
            clf.confidence,
            parse_confidence=parsed.parse_confidence,
            is_known_merchant=is_known_merchant,
            location_match=location_label is not None,
        )

        # ── Implicit Refund detection ─────────────────────────
        # If it's a credit but not classified explicitly as income or transfer,
        # it is likely a refund from an expense merchant (e.g. Swiggy, Amazon).
        if parsed.tx_type == "credit" and not clf.is_income and not clf.is_transfer and not clf.is_refund:
            clf.is_refund = True

        is_recurring = match_keyword(sms_text, RECURRING_KEYWORDS)
        tags = []
        net_amount = parsed.amount

        if is_recurring:
            tags.append("recurring")

        if clf.is_refund:
            tags.append("refund")
            net_amount = 0.0

        if clf.is_wallet_load:
            tags.append("wallet_load")
            net_amount = 0.0

        if clf.is_income:
            tags.append("income")

        # ── Mixed basket detection ─────────────────────────
        is_mixed = is_mixed_basket_merchant(parsed.merchant or "", parsed.amount or 0)
        if is_mixed:
            tags.append("mixed_basket")

        # ── Cashback detection ─────────────────────────────
        is_cb = is_cashback_transaction(sms_text, parsed.vpa)
        if is_cb:
            tags.append("cashback")
            net_amount = 0.0

        # ── Deposit detection ──────────────────────────────
        is_dep = is_deposit_transaction(sms_text)
        if is_dep:
            tags.append("deposit")

        # ── P2P detection ─────────────────────────────────
        needs_p2p_review = False
        is_p2p = False
        if parsed.vpa and is_p2p_vpa(parsed.vpa):
            is_p2p = True
            
        text_lower = sms_text.lower()
        if "received from" in text_lower and "via upi" in text_lower:
            is_p2p = True
        elif "paid to" in text_lower and "via upi" in text_lower:
            is_p2p = True
        elif "sent to" in text_lower and "via upi" in text_lower:
            is_p2p = True

        if is_p2p:
            needs_p2p_review = True
            tags.append("p2p")
            clf.category = "Uncategorised"
            clf.sub_category = "Needs Review"
            clf.confidence = 0.0
            score.action = ConfidenceAction.ASK_USER
            score.adjusted = 0.0

        # ── Subscription detection ─────────────────────────
        is_subscription = any(
            kw in sms_text.upper()
            for kw in ["NETFLIX", "SPOTIFY", "HOTSTAR", "PRIME", "ZEE5", "SUBSCRIPTION", "SONY LIV"]
        )
        needs_subscription_review = is_subscription and (parsed.amount or 0) > 500

        # ── Determine review status based on confidence ─────────────────────────
        if score.action == ConfidenceAction.AUTO_ASSIGN and not is_mixed:
            review_status = ReviewStatus.REVIEWED

        elif clf.category == "Uncategorised" or score.adjusted < settings.confidence_suggest:
            review_status = ReviewStatus.PENDING

            # Prevent bad data from polluting dashboard
            clf.category = "Uncategorised"
            clf.sub_category = "Needs Review"

        else:
            review_status = ReviewStatus.PENDING

        needs_salary_review = False
        if parsed.tx_type == "credit" and (parsed.amount or 0) > 15000 and clf.category in ["Uncategorised", "Income"]:
            needs_salary_review = True
            tags.append("potential_salary")

        basket_splits_default = None
        if is_mixed:
            # Smart Defaults for mixed basket
            basket_splits_default = json.dumps([
                {"category": "Groceries", "percentage": 60},
                {"category": "Personal Care", "percentage": 40}
            ])

        # Festival Framing
        explanation = clf.explanation or ""
        month_day = (parsed.tx_date or datetime.utcnow()).strftime("%m-%d")
        if "10-20" <= month_day <= "11-15": # Example Diwali Window
            explanation += " (Occurred during festive season)"

        # ── Create transaction ─────────────────────────
        tx = Transaction(
            user_id=self.user_id,
            raw_sms=sms_text,
            bank=parsed.bank,
            amount=parsed.amount,
            tx_type=TransactionType(parsed.tx_type or "debit"),
            tx_date=parsed.tx_date or datetime.utcnow(),
            merchant=parsed.merchant,
            vpa=parsed.vpa,
            account_ref=parsed.account_ref,
            payment_method=parsed.payment_method,
            category=clf.category,
            sub_category=clf.sub_category,
            confidence=score.adjusted,
            explanation=explanation,
            is_recurring=is_recurring,
            is_income=clf.is_income,
            is_refund=clf.is_refund,
            is_transfer=clf.is_transfer,
            is_wallet_load=clf.is_wallet_load,
            is_cashback=is_cb,
            is_deposit=is_dep,
            is_mixed_basket=is_mixed,
            basket_splits=basket_splits_default,
            net_amount=net_amount,
            tags=",".join(tags) if tags else None,
            review_status=review_status,
            location_lat=location_lat,
            location_lon=location_lon,
            location_label=location_label,
        )

        self.db.add(tx)
        await self.db.flush()

        # ── Wallet Float tracking ──────────────────────────────
        if clf.is_wallet_load and parsed.merchant:
            wallet_name = parsed.merchant.lower()
            stmt = select(WalletFloat).where(WalletFloat.user_id == self.user_id, WalletFloat.wallet_name == wallet_name)
            res = await self.db.execute(stmt)
            wallet = res.scalar_one_or_none()
            if not wallet:
                wallet = WalletFloat(
                    user_id=self.user_id, 
                    wallet_name=wallet_name, 
                    loaded_amount=0.0,
                    remaining_float=0.0,
                    load_tx_id=tx.id
                )
                self.db.add(wallet)
            wallet.loaded_amount += (parsed.amount or 0)
            wallet.remaining_float += (parsed.amount or 0)

        # ── Refund / Cashback Linking ──────────────────────────────
        if clf.is_refund and parsed.merchant:
            # Lookback 30 days for original debit to same merchant
            lookback = tx.tx_date - timedelta(days=30)
            stmt = select(Transaction).where(
                Transaction.user_id == self.user_id,
                Transaction.merchant == parsed.merchant,
                Transaction.tx_type == TransactionType.DEBIT,
                Transaction.tx_date >= lookback,
                Transaction.net_amount > 0,
                # Match where refund is at least 80% of the original debit amount
                Transaction.amount >= (parsed.amount or 0),
                (parsed.amount or 0) >= 0.8 * Transaction.amount
            ).order_by(Transaction.tx_date.desc()).limit(1)
            
            res = await self.db.execute(stmt)
            orig_tx = res.scalar_one_or_none()
            if orig_tx:
                orig_tx.net_amount = max(0.0, orig_tx.net_amount - (parsed.amount or 0))
                tx.original_tx_id = orig_tx.id
        
        if is_cb and parsed.merchant:
            # Lookback 30 days
            lookback = tx.tx_date - timedelta(days=30)
            stmt = select(Transaction).where(
                Transaction.user_id == self.user_id,
                Transaction.merchant == parsed.merchant,
                Transaction.tx_type == TransactionType.DEBIT,
                Transaction.tx_date >= lookback,
                Transaction.net_amount > 0
            ).order_by(Transaction.tx_date.desc()).limit(1)
            
            res = await self.db.execute(stmt)
            orig_tx = res.scalar_one_or_none()
            if orig_tx:
                orig_tx.net_amount = max(0.0, orig_tx.net_amount - (parsed.amount or 0))

        output = tx.to_output_dict()
        output["confidence_action"] = score.action.value
        output["confidence_display"] = score.display_label
        output["needs_user_input"] = clf.needs_user_input
        output["needs_p2p_review"] = needs_p2p_review
        output["needs_subscription_review"] = needs_subscription_review
        output["needs_salary_review"] = needs_salary_review
        output["is_mixed_basket"] = is_mixed

        if clf.suggested_options:
            output["suggested_options"] = clf.suggested_options

        return output

    async def correct_category(
        self, transaction_id: int, category: str, sub_category: str, is_reimbursement: bool = False
    ) -> dict:
        await self._learning_service.record_correction(
            self.user_id, transaction_id, category, sub_category
        )

        tx = await self.db.get(Transaction, transaction_id)
        if tx and is_reimbursement:
            existing_tags = tx.tags.split(",") if tx.tags else []
            if "reimbursement" not in existing_tags:
                existing_tags.append("reimbursement")
            tx.tags = ",".join(existing_tags)
            await self.db.commit()

        return tx.to_output_dict() if tx else {"error": "Not found"}