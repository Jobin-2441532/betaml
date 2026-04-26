from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from app.utils.patterns import SMS_TEMPLATES, ATM_KEYWORDS, match_keyword


@dataclass
class ParsedSMS:
    amount: Optional[float] = None
    tx_type: Optional[str] = None
    merchant: Optional[str] = None
    vpa: Optional[str] = None
    account_ref: Optional[str] = None
    bank: Optional[str] = None
    tx_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    raw_text: str = ""
    parse_confidence: float = 0.0
    errors: list = field(default_factory=list)


class SMSParser:
    AMOUNT_RE  = re.compile(r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
    AMOUNT_RE2 = re.compile(r"([\d,]+(?:\.\d{1,2})?)\s*(?:Rs\.?|INR|₹)", re.IGNORECASE)
    VPA_RE     = re.compile(r"([a-zA-Z0-9.\-_]+@[a-zA-Z]+)", re.IGNORECASE)

    DATE_PATTERNS = [
        (r"(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})", "%d-%m-%Y %H:%M:%S"),
        (r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", "%d/%m/%Y %H:%M:%S"),
        (r"(\d{2}-\d{2}-\d{4})", "%d-%m-%Y"),
        (r"(\d{2}/\d{2}/\d{4})", "%d/%m/%Y"),
        (r"(\d{4}-\d{2}-\d{2})", "%Y-%m-%d"),
        (r"(\d{2}\s+\w{3}\s+\d{4})", "%d %b %Y"),
    ]

    DEBIT_WORDS  = {"debited", "paid", "withdrawn", "deducted", "spent"}
    CREDIT_WORDS = {"credited", "received", "deposited", "added", "refunded"}

    PM_RULES = [
        ("ATM", ["atm", "cash withdrawal", "atm wdl"]),
        ("UPI", ["upi", "vpa", "@"]),
        ("CARD", ["pos", "card", "swipe", "contactless"]),
        ("WALLET", ["wallet", "paytm balance"]),
        ("NEFT", ["neft"]),
        ("IMPS", ["imps"]),
        ("NACH", ["nach", "ecs", "mandate"]),
    ]

    def parse(self, sms_text: str) -> ParsedSMS:
        result = ParsedSMS(raw_text=sms_text)
        text = sms_text.strip()

        if not self._try_templates(text, result) or result.amount is None:
            self._extract_amount(text, result)

        if result.tx_type is None:
            self._extract_tx_type(text, result)

        if result.vpa is None:
            self._extract_vpa(text, result)

        if result.tx_date is None:
            self._extract_date(text, result)

        self._detect_payment_method(text, result)

        # ── Better merchant extraction ─────────────────────────────
        if not result.merchant and result.vpa:
            vpa_prefix = result.vpa.split("@")[0]
            result.merchant = vpa_prefix

        if result.merchant:
            result.merchant = self._clean_merchant(result.merchant)

        if not result.merchant or result.merchant.lower() in ("unknown", ""):
            self._extract_merchant_from_text(text, result)

        result.parse_confidence = self._compute_confidence(result)
        return result

    def _try_templates(self, text: str, result: ParsedSMS) -> bool:
        for tpl in SMS_TEMPLATES:
            m = re.search(tpl["pattern"], text, re.IGNORECASE | re.DOTALL)
            if m:
                gd = m.groupdict()
                if gd.get("amount"):
                    result.amount = float(gd["amount"].replace(",", ""))
                if gd.get("vpa"):
                    result.vpa = gd["vpa"].lower()

                for kw, ttype in tpl["type_keywords"].items():
                    if kw in text.lower():
                        result.tx_type = ttype
                        break

                result.bank = tpl["bank"]
                return True
        return False

    def _extract_amount(self, text: str, result: ParsedSMS) -> None:
        for pat in (self.AMOUNT_RE, self.AMOUNT_RE2):
            m = pat.search(text)
            if m:
                result.amount = float(m.group(1).replace(",", ""))
                return
        result.errors.append("amount_not_found")

    def _extract_tx_type(self, text: str, result: ParsedSMS) -> None:
        lower = text.lower()
        for w in self.DEBIT_WORDS:
            if w in lower:
                result.tx_type = "debit"
                return
        for w in self.CREDIT_WORDS:
            if w in lower:
                result.tx_type = "credit"
                return
        result.errors.append("tx_type_not_found")

    def _extract_vpa(self, text: str, result: ParsedSMS) -> None:
        m = self.VPA_RE.search(text)
        if m:
            result.vpa = m.group(1).lower()
            if not result.merchant:
                result.merchant = result.vpa.split("@")[0]

    def _extract_date(self, text: str, result: ParsedSMS) -> None:
        for pattern, fmt in self.DATE_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    result.tx_date = datetime.strptime(m.group(1).strip(), fmt)
                    return
                except ValueError:
                    continue

        result.tx_date = datetime.utcnow()
        result.errors.append("date_fallback_to_now")

    def _detect_payment_method(self, text: str, result: ParsedSMS) -> None:
        lower = text.lower()

        if match_keyword(text.upper(), ATM_KEYWORDS):
            result.payment_method = "ATM"
            return

        for method, keywords in self.PM_RULES:
            if any(kw in lower for kw in keywords):
                result.payment_method = method
                return

        result.payment_method = "UNKNOWN"

    def _extract_merchant_from_text(self, text: str, result: ParsedSMS) -> None:
        patterns = [
            r"(?:to|at)\s+([A-Z][A-Z0-9\s&.\-]{2,30}?)(?:\s+(?:via|on|Ref|\d))",
            r"(?:NEFT from|IMPS from|credited by)\s+([A-Z][A-Z\s&.]{3,30}?)(?:\s+Ref)",
            r"(?:POS TXN at|POS at)\s+([A-Z][A-Z\s\-]{3,35}?)(?:\s+on|\d)",
            r"(?:Narration:|Info:|Remarks:)\s*([A-Z0-9_\s]{3,25})",
            r"from\s+([A-Z][a-zA-Z\s]{2,20})",
            r"paid to\s+([A-Z][A-Z0-9\s&.\-]{2,30}?)(?:\s+(?:via|on|\.))",
            r"([A-Z]+)\s+ORDER CANCELLED",
            r"REFUND\s+FROM\s+([A-Z][a-zA-Z\s]{2,20})",
        ]

        for pattern in patterns:
            m = re.search(pattern, text.upper())
            if m:
                raw = m.group(1).strip()

                skip = {"YOUR", "THE", "FROM", "INTO", "ACCOUNT",
                        "BALANCE", "VPA", "UPI", "REF", "HDFC",
                        "ICICI", "SBI", "AXIS", "KOTAK"}

                if raw not in skip and len(raw) > 2:
                    result.merchant = raw[:40].title()
                    return

        # Fallback to known high-confidence merchants
        from app.utils.patterns import LAYER_1_STRICT, LAYER_2_HIGH
        text_lower = text.lower()
        for m_key in list(LAYER_1_STRICT.keys()) + list(LAYER_2_HIGH.keys()):
            if len(m_key) > 3 and m_key in text_lower:
                if re.search(rf"\b{re.escape(m_key)}\b", text_lower):
                    result.merchant = m_key.title()
                    return

    @staticmethod
    def _clean_merchant(name: str) -> str:
        name = re.sub(r"[^a-zA-Z0-9 &._-]", " ", name)
        return re.sub(r"\s+", " ", name).strip().title()

    @staticmethod
    def _compute_confidence(result: ParsedSMS) -> float:
        score = 1.0
        if result.amount is None: score -= 0.5
        if result.tx_type is None: score -= 0.2
        score -= 0.05 * len(result.errors)
        return max(0.0, round(score, 2))