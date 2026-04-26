from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from config.settings import settings

@dataclass
class RawTransaction:
    id: int
    amount: float
    tx_type: str       # "debit" | "credit"
    tx_date: datetime
    merchant: Optional[str] = None
    vpa: Optional[str] = None

@dataclass
class SplitGroupResult:
    anchor_tx_id: int
    credit_tx_ids: list
    total_debit: float
    total_credited: float
    net_expense: float
    member_count: int
    status: str        # "open" | "partial" | "settled"
    confidence: float
    explanation: str

class SplitEngine:
    TOLERANCE = 0.05   # 5% tolerance for sum match

    def __init__(self, window_days: int = settings.split_window_days):
        self.window_days = window_days

    def detect_splits(self, transactions: list) -> list:
        results = []
        debits = [t for t in transactions
                  if t.tx_type == "debit" and t.amount >= settings.split_min_amount]
        processed: set = set()

        for debit in debits:
            window_end = debit.tx_date + timedelta(days=self.window_days)
            window_start = debit.tx_date - timedelta(days=7)
            candidates = [
                t for t in transactions
                if t.tx_type == "credit"
                and t.id not in processed
                and window_start <= t.tx_date <= window_end
                and t.amount < debit.amount
                and t.amount >= settings.split_min_amount
            ]
            if not candidates:
                continue

            selected, total_credit = self._find_subset(debit.amount, candidates)
            if not selected:
                continue

            net = round(debit.amount - total_credit, 2)
            member_count = len(selected) + 1
            per_person = round(debit.amount / member_count, 2)

            div_ok = all(
                abs(c.amount - per_person) / (per_person or 1) <= 0.15
                for c in selected
            )
            conf = 0.75
            if div_ok: conf += 0.15
            if abs(total_credit - (debit.amount - per_person)) / (debit.amount or 1) <= self.TOLERANCE:
                conf += 0.05
            conf = min(round(conf, 4), 0.99)

            status = (
                "settled" if net <= per_person * 0.10
                else "partial" if total_credit > 0
                else "open"
            )
            results.append(SplitGroupResult(
                anchor_tx_id=debit.id,
                credit_tx_ids=[c.id for c in selected],
                total_debit=debit.amount,
                total_credited=round(total_credit, 2),
                net_expense=net,
                member_count=member_count,
                status=status, confidence=conf,
                explanation=(
                    f"Detected {len(selected)}-person split for ₹{debit.amount:.0f}. "
                    f"Received ₹{total_credit:.0f} back. Net expense: ₹{net:.0f}."
                ),
            ))
            processed.update(c.id for c in selected)
        return results

    def _find_subset(self, target: float, candidates: list):
        best_subset, best_diff, best_sum = [], float("inf"), 0.0
        for n in range(2, min(len(candidates) + 2, 9)):
            expected = target * (n - 1) / n
            per = target / n
            chosen = sorted(candidates, key=lambda c: abs(c.amount - per))[:n - 1]
            chosen_sum = sum(c.amount for c in chosen)
            diff = abs(chosen_sum - expected) / (target or 1)
            if diff < best_diff and diff <= self.TOLERANCE * 2:
                best_diff, best_subset, best_sum = diff, chosen, chosen_sum
        return best_subset, best_sum