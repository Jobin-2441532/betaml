"""app/core/classifier.py - Hybrid transaction classifier."""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from app.core.sms_parser import ParsedSMS
from app.utils.patterns import (
    ATM_KEYWORDS, INCOME_KEYWORDS, REFUND_KEYWORDS,
    get_category_from_keywords, get_category_from_vpa,
    match_keyword,
)
from config.settings import settings


@dataclass
class ClassificationResult:
    category: str
    sub_category: str
    confidence: float
    explanation: str
    is_income: bool = False
    is_refund: bool = False
    is_transfer: bool = False
    is_atm: bool = False
    is_wallet_load: bool = False
    needs_user_input: bool = False
    suggested_options: list = field(default_factory=list)


class HybridClassifier:

    TRANSFER_RE = re.compile(
        r"\b(self transfer|own account|sweep|fd sweep)\b", re.IGNORECASE
    )
    WALLET_RE = re.compile(
        r"\b(wallet (load|topup|recharge)|add money to wallet|paytm wallet|"
        r"phonepe wallet|amazon pay wallet)\b",
        re.IGNORECASE,
    )
    FASTAG_RE = re.compile(
        r"\b(fastag|fas.?tag|toll|nhai|ihmcl|netc|nh\d+|toll plaza)\b",
        re.IGNORECASE,
    )

    def __init__(self, merchant_mappings: dict | None = None):
        self.merchant_mappings = merchant_mappings or {}
        self._ml_model = None
        self._ml_model_mtime = None

    def classify(self, parsed: ParsedSMS) -> ClassificationResult:
        text = self._feature_text(parsed)
        upper = text.upper()
        raw_upper = (parsed.raw_text or "").upper()
        
        from app.utils.patterns import LAYER_1_STRICT, LAYER_2_HIGH, LAYER_3_KEYWORDS, is_mixed_basket_merchant

        # ── Layer 0: Hard rules ───────────────────────────────────────────────
        hard = self._hard_rules(text, upper, raw_upper, parsed)
        if hard:
            return hard

        # ── Layer 1: User merchant mappings (Explicit Overrides) ─────────────
        # Check merchant name
        if parsed.merchant:
            key = parsed.merchant.lower().strip()
            if key in self.merchant_mappings:
                cat, sub = self.merchant_mappings[key]
                return ClassificationResult(
                    category=cat, sub_category=sub, confidence=0.99,
                    explanation=f"Categorised based on your correction for '{parsed.merchant}'.",
                )

        # Check VPA prefix in mappings
        if parsed.vpa:
            vpa_prefix = parsed.vpa.split("@")[0].lower().strip()
            if vpa_prefix in self.merchant_mappings:
                cat, sub = self.merchant_mappings[vpa_prefix]
                return ClassificationResult(
                    category=cat, sub_category=sub, confidence=0.99,
                    explanation=f"Categorised based on your correction for '{vpa_prefix}'.",
                )
            full_vpa = parsed.vpa.lower().strip()
            if full_vpa in self.merchant_mappings:
                cat, sub = self.merchant_mappings[full_vpa]
                return ClassificationResult(
                    category=cat, sub_category=sub, confidence=0.99,
                    explanation=f"Categorised based on your correction for '{full_vpa}'.",
                )

        if self.merchant_mappings and parsed.raw_text:
            sms_lower = parsed.raw_text.lower()
            for key, (cat, sub) in self.merchant_mappings.items():
                if len(key) >= 3 and key in sms_lower:
                    return ClassificationResult(
                        category=cat, sub_category=sub, confidence=0.99,
                        explanation=f"Categorised based on your correction ('{key}' found in SMS).",
                    )

        # Build feature text list to check layers
        search_terms = []
        if parsed.merchant: search_terms.append(parsed.merchant.lower().strip())
        if parsed.vpa:
            search_terms.append(parsed.vpa.split("@")[0].lower().strip())

        # ── Layer 2: Strict Whitelist (Near 100% Confidence) ─────────────────
        for term in search_terms:
            if term in LAYER_1_STRICT:
                cat, sub = LAYER_1_STRICT[term]
                return ClassificationResult(
                    category=cat, sub_category=sub, confidence=0.99,
                    explanation=f"Strict brand match for '{term}'.",
                )

        # ── Layer 3: High Confidence / Broad Category ────────────────────────
        for term in search_terms:
            if term in LAYER_2_HIGH:
                cat, sub = LAYER_2_HIGH[term]
                # If mixed basket and amount > 800, lower confidence to force review
                amount = parsed.amount or 0
                is_mixed = is_mixed_basket_merchant(term, amount)
                conf = 0.60 if (is_mixed and amount > 800) else 0.85
                explanation = (
                    f"Mixed basket purchase > ₹800 needs review." if conf == 0.60 
                    else f"Broad category match for '{term}'."
                )
                return ClassificationResult(
                    category=cat, sub_category=sub, confidence=conf,
                    explanation=explanation,
                )

        # ── Layer 4: Smart Keyword Engine (Local Merchants) ──────────────────
        text_lower = text.lower()
        for kw, (cat, sub) in LAYER_3_KEYWORDS.items():
            if kw in text_lower:
                return ClassificationResult(
                    category=cat, sub_category=sub, confidence=0.60,
                    explanation=f"Local merchant keyword match for '{kw}'.",
                )

        # ── Layer 4.5: VPA pattern & old keywords (Fallback) ─────────────────
        if parsed.vpa:
            vpa_cat = get_category_from_vpa(parsed.vpa)
            if vpa_cat:
                _, sub, _ = get_category_from_keywords(parsed.vpa.split("@")[0])
                return ClassificationResult(
                    category=vpa_cat, sub_category=sub or "General", confidence=0.75,
                    explanation=f"Categorised as {vpa_cat} via UPI ID '{parsed.vpa}'.",
                )

        kw_cat, kw_sub, kw_conf = get_category_from_keywords(text)
        if kw_cat and kw_conf >= 0.60:
            return ClassificationResult(
                category=kw_cat, sub_category=kw_sub or "General",
                confidence=0.60, # max out at 0.60 to force review or suggestion
                explanation=f"Categorised as {kw_cat} via general keyword match.",
            )

        # ── Layer 5: ML model ─────────────────────────────────────────────────
        ml_model = self._get_ml_model()
        if ml_model:
            ml = self._ml_predict(ml_model, text)
            if ml and ml.confidence >= 0.40:
                if kw_cat and kw_conf >= 0.3:
                    ml.confidence = round(0.4 * kw_conf + 0.6 * ml.confidence, 4)
                return ml

        # ── Fallback ──────────────────────────────────────────────────────────
        return self._fallback(kw_cat, kw_conf, parsed)

    def update_merchant_mapping(self, merchant: str, category: str, sub_category: str):
        if merchant:
            self.merchant_mappings[merchant.lower().strip()] = (category, sub_category)

    # ── Private ───────────────────────────────────────────────────────────────

    def _hard_rules(
        self, text: str, upper: str, raw_upper: str, parsed: ParsedSMS
    ) -> Optional[ClassificationResult]:

        # ATM
        if match_keyword(upper, ATM_KEYWORDS) or parsed.payment_method == "ATM":
            return ClassificationResult(
                category="Cash Withdrawal", sub_category="ATM",
                confidence=0.60, explanation="ATM cash withdrawal needs review.",
                is_atm=True,
            )

        # FASTag / Toll
        if self.FASTAG_RE.search(raw_upper or upper):
            return ClassificationResult(
                category="Transport", sub_category="Toll",
                confidence=0.97,
                explanation="Categorised as Transport (Toll) - FASTag/toll payment detected.",
            )

        # Refund
        if match_keyword(upper, REFUND_KEYWORDS):
            return ClassificationResult(
                category="Refund", sub_category="Refund",
                confidence=0.95, explanation="Refund or reversal detected.",
                is_refund=True,
            )

        # Income (credit + income keywords)
        if parsed.tx_type == "credit" and match_keyword(upper, INCOME_KEYWORDS):
            sub = "Salary" if "SALARY" in upper else "Income"
            return ClassificationResult(
                category="Income", sub_category=sub,
                confidence=0.93, explanation=f"Income detected - {sub}.",
                is_income=True,
            )

        # Self transfer
        if self.TRANSFER_RE.search(text):
            return ClassificationResult(
                category="Personal Transfer", sub_category="Self Transfer",
                confidence=0.95, explanation="Self-transfer pattern detected.",
                is_transfer=True,
            )

        # Wallet load
        if self.WALLET_RE.search(text):
            return ClassificationResult(
                category="Wallet", sub_category="Load",
                confidence=0.92, explanation="Wallet top-up detected.",
                is_wallet_load=True,
            )

        # Debit card POS - should NOT be credit card
        # Only classify as credit card if SMS explicitly says so
        if parsed.payment_method == "CARD" and parsed.tx_type == "debit":
            if not any(kw in upper for kw in
                       ["CREDIT CARD", "CC PAYMENT", "CC PMT",
                        "CREDIT CARD BILL", "CC BILL"]):
                pass  # Fall through to keyword/ML classification

        return None

    def _ml_predict(self, model, text: str) -> Optional[ClassificationResult]:
        try:
            import numpy as np
            proba = model.predict_proba([text])[0]
            idx = int(np.argmax(proba))
            conf = float(proba[idx])
            cat = model.classes_[idx]
            return ClassificationResult(
                category=cat, sub_category="General",
                confidence=round(conf, 4),
                explanation=f"ML model predicted {cat} ({conf:.0%} confidence).",
            )
        except Exception as e:
            return None

    def _fallback(
        self, kw_cat: Optional[str], kw_conf: float, parsed: ParsedSMS
    ) -> ClassificationResult:
        if kw_cat and kw_conf >= 0.3:
            return ClassificationResult(
                category=kw_cat, sub_category="General",
                confidence=round(kw_conf, 4),
                explanation=f"Possible match: {kw_cat}. Please confirm.",
                needs_user_input=True,
                suggested_options=[kw_cat, "Food & Dining", "Transport",
                                   "Shopping", "Others"],
            )
        return ClassificationResult(
            category="Uncategorised", sub_category="Needs Review",
            confidence=0.0,
            explanation="Could not classify. Please review manually.",
            needs_user_input=True,
            suggested_options=["Food & Dining", "Transport", "Entertainment",
                               "Shopping", "Health", "Others"],
        )

    @staticmethod
    def _feature_text(parsed: ParsedSMS) -> str:
        parts = []
        if parsed.merchant:
            parts.append(parsed.merchant)
        if parsed.vpa:
            parts.append(parsed.vpa)
            parts.append(parsed.vpa.split("@")[0])
        if parsed.raw_text:
            parts.append(parsed.raw_text[:300])
        return " ".join(parts).lower()

    def _get_ml_model(self):
        """Load model fresh if file has changed since last load."""
        try:
            import joblib
            path = settings.model_path
            # ✅ FIX: Resolve relative paths from project root, not CWD
            if not os.path.isabs(path):
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                path = os.path.join(project_root, path)
            if not os.path.exists(path):
                return None
            mtime = os.path.getmtime(path)
            if self._ml_model is None or mtime != self._ml_model_mtime:
                self._ml_model = joblib.load(path)
                self._ml_model_mtime = mtime
            return self._ml_model
        except Exception:
            return None