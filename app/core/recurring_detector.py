from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from app.utils.patterns import RECURRING_KEYWORDS, match_keyword

@dataclass
class RecurringCandidate:
    merchant: str
    category: str
    sub_category: str
    amount: float
    frequency: str
    occurrences: int
    last_seen: datetime
    next_expected: Optional[datetime]
    confidence: float

class RecurringDetector:
    FREQ_WINDOWS = {
        "weekly":  (5, 9),
        "monthly": (25, 35),
        "annual":  (355, 375),
    }
    AMOUNT_TOLERANCE = 0.10

    def detect(self, transactions: list) -> list:
        candidates = []

        # Pass 1: Keyword detection (NACH, ECS, BBPS etc.)
        for tx in transactions:
            if tx.get("tx_type") != "debit": continue
            raw = (tx.get("raw_text") or "") + " " + (tx.get("merchant") or "")
            if match_keyword(raw, RECURRING_KEYWORDS):
                candidates.append(self._build(tx, 0.92))

        # Pass 2: Pattern detection (same merchant, similar amount, regular interval)
        by_merchant: dict = defaultdict(list)
        for tx in transactions:
            if tx.get("tx_type") == "debit" and tx.get("merchant"):
                by_merchant[tx["merchant"].lower().strip()].append(tx)

        for _, txs in by_merchant.items():
            if len(txs) < 2: continue
            txs_sorted = sorted(txs, key=lambda t: t["tx_date"])
            result = self._analyse(txs_sorted)
            if result:
                freq, conf = result
                last = txs_sorted[-1]
                candidates.append(RecurringCandidate(
                    merchant=last["merchant"],
                    category=last.get("category", "Uncategorised"),
                    sub_category=last.get("sub_category", ""),
                    amount=last["amount"], frequency=freq,
                    occurrences=len(txs_sorted), last_seen=last["tx_date"],
                    next_expected=self._next(last["tx_date"], freq),
                    confidence=round(conf, 4),
                ))

        # Deduplicate
        seen: set = set()
        return [c for c in candidates
                if c.merchant.lower() not in seen
                and not seen.add(c.merchant.lower())]

    def _build(self, tx: dict, conf: float) -> RecurringCandidate:
        return RecurringCandidate(
            merchant=tx.get("merchant", "Unknown"),
            category=tx.get("category", "Uncategorised"),
            sub_category=tx.get("sub_category", ""),
            amount=tx["amount"], frequency="monthly", occurrences=1,
            last_seen=tx["tx_date"],
            next_expected=self._next(tx["tx_date"], "monthly"),
            confidence=conf,
        )

    def _analyse(self, txs: list):
        intervals = [(txs[i]["tx_date"] - txs[i-1]["tx_date"]).days
                     for i in range(1, len(txs))]
        avg = sum(intervals) / len(intervals)
        variance = sum(abs(d - avg) for d in intervals) / len(intervals)
        if variance > avg * 0.3: return None

        amounts = [t["amount"] for t in txs]
        avg_amt = sum(amounts) / len(amounts)
        if any(abs(a - avg_amt) / (avg_amt or 1) > self.AMOUNT_TOLERANCE for a in amounts):
            return None

        for freq, (lo, hi) in self.FREQ_WINDOWS.items():
            if lo <= avg <= hi:
                return freq, 0.70 + min(len(txs) * 0.05, 0.25)
        return None

    @staticmethod
    def _next(last: datetime, frequency: str) -> datetime:
        return last + timedelta(days={"weekly": 7, "monthly": 30, "annual": 365}.get(frequency, 30))