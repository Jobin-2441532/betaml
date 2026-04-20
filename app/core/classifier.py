from __future__ import annotations
import os, re
from dataclasses import dataclass, field
from typing import Optional
import joblib
import numpy as np
from app.core.sms_parser import ParsedSMS
from app.utils.patterns import (
    ATM_KEYWORDS, INCOME_KEYWORDS, REFUND_KEYWORDS,
    get_category_from_keywords, get_category_from_vpa, match_keyword,
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
        r"\b(wallet (load|topup|recharge)|add money to wallet)\b", re.IGNORECASE
    )

    def __init__(self, merchant_mappings: dict | None = None):
        self.merchant_mappings = merchant_mappings or {}
        self._ml_model = self._load_ml_model()

    def classify(self, parsed: ParsedSMS) -> ClassificationResult:
        text = self._feature_text(parsed)
        upper = text.upper()

        # Layer 1: Hard rules (highest priority)
        override = self._hard_rules(text, upper, parsed)
        if override:
            return override

        # Layer 2: User's personal merchant mapping
        if parsed.merchant:
            key = parsed.merchant.lower().strip()
            if key in self.merchant_mappings:
                cat, sub = self.merchant_mappings[key]
                return ClassificationResult(
                    category=cat, sub_category=sub, confidence=0.99,
                    explanation=f"Based on your previous correction for '{parsed.merchant}'.",
                )

        # Layer 3a: VPA pattern match
        if parsed.vpa:
            vpa_cat = get_category_from_vpa(parsed.vpa)
            if vpa_cat:
                _, sub, _ = get_category_from_keywords(parsed.vpa.split("@")[0])
                return ClassificationResult(
                    category=vpa_cat, sub_category=sub or "General", confidence=0.90,
                    explanation=f"Categorised as {vpa_cat} via UPI VPA '{parsed.vpa}'.",
                )

        # Layer 3b: Keyword match
        kw_cat, kw_sub, kw_conf = get_category_from_keywords(text)
        if kw_cat and kw_conf >= 0.60:
            return ClassificationResult(
                category=kw_cat, sub_category=kw_sub or "General", confidence=kw_conf,
                explanation=f"Categorised as {kw_cat} via keyword match.",
            )

        # Layer 4: ML model (if trained and available)
        if self._ml_model:
            ml = self._ml_predict(text)
            if ml:
                if kw_cat and kw_conf >= 0.3:
                    ml.confidence = round(0.4 * kw_conf + 0.6 * ml.confidence, 4)
                return ml

        # Fallback: ask user
        return self._p2p_fallback(kw_cat, kw_conf)

    def update_merchant_mapping(self, merchant: str, category: str, sub_category: str):
        self.merchant_mappings[merchant.lower().strip()] = (category, sub_category)

    def _hard_rules(self, text, upper, parsed) -> Optional[ClassificationResult]:
        if match_keyword(upper, ATM_KEYWORDS) or parsed.payment_method == "ATM":
            return ClassificationResult(
                category="Cash Withdrawal", sub_category="ATM", confidence=0.97,
                explanation="ATM/Cash withdrawal detected.", is_atm=True,
            )
        if match_keyword(upper, REFUND_KEYWORDS):
            return ClassificationResult(
                category="Refund", sub_category="Refund", confidence=0.95,
                explanation="Refund or reversal keyword detected.", is_refund=True,
            )
        if parsed.tx_type == "credit" and match_keyword(upper, INCOME_KEYWORDS):
            sub = "Salary" if "SALARY" in upper else "Income"
            return ClassificationResult(
                category="Income", sub_category=sub, confidence=0.93,
                explanation=f"Income keyword detected – classified as {sub}.", is_income=True,
            )
        if self.TRANSFER_RE.search(text):
            return ClassificationResult(
                category="Personal Transfer", sub_category="Self Transfer", confidence=0.95,
                explanation="Self-transfer pattern detected.", is_transfer=True,
            )
        if self.WALLET_RE.search(text):
            return ClassificationResult(
                category="Wallet", sub_category="Load", confidence=0.92,
                explanation="Wallet top-up detected.", is_wallet_load=True,
            )
        return None

    def _ml_predict(self, text: str) -> Optional[ClassificationResult]:
        try:
            proba = self._ml_model.predict_proba([text])[0]
            idx = int(np.argmax(proba))
            conf = float(proba[idx])
            cat = self._ml_model.classes_[idx]
            return ClassificationResult(
                category=cat, sub_category="General", confidence=round(conf, 4),
                explanation=f"ML model predicted {cat} ({conf:.0%} confidence).",
            )
        except Exception:
            return None

    def _p2p_fallback(self, kw_cat, kw_conf) -> ClassificationResult:
        if kw_cat and kw_conf >= 0.3:
            return ClassificationResult(
                category=kw_cat, sub_category="General", confidence=round(kw_conf, 4),
                explanation=f"Weak keyword match for {kw_cat}. Please confirm.",
                needs_user_input=True,
                suggested_options=[kw_cat, "Food & Dining", "Transport", "Shopping", "Others"],
            )
        return ClassificationResult(
            category="Uncategorised", sub_category="P2P / Unknown", confidence=0.0,
            explanation="Could not determine category. Please categorise manually.",
            needs_user_input=True,
            suggested_options=["Food & Dining", "Transport", "Entertainment", "Shopping", "Others"],
        )

    @staticmethod
    def _feature_text(parsed: ParsedSMS) -> str:
        parts = []
        if parsed.merchant: parts.append(parsed.merchant)
        if parsed.vpa:      parts.append(parsed.vpa)
        if parsed.raw_text: parts.append(parsed.raw_text[:200])
        return " ".join(parts).lower()

    @staticmethod
    def _load_ml_model():
        if os.path.exists(settings.model_path):
            try:
                return joblib.load(settings.model_path)
            except Exception:
                pass
        return None