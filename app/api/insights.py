from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.recurring_detector import RecurringDetector
from app.models.transaction import Transaction, TransactionType
from app.utils.db import get_db

router = APIRouter()

@router.get("/monthly-summary")
async def monthly_summary(user_id: int, year: int, month: int, db: AsyncSession = Depends(get_db)):
    from_date = datetime(year, month, 1)
    to_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    stmt = select(Transaction).where(Transaction.user_id == user_id,
                                     Transaction.tx_date >= from_date, Transaction.tx_date < to_date)
    result = await db.execute(stmt)
    txs = result.scalars().all()

    cat_spend: dict = defaultdict(float)
    total_income = total_expense = total_refunds = 0.0

    for tx in txs:
        if tx.is_refund or tx.is_wallet_load:
            total_refunds += tx.amount; continue
        if tx.is_income or tx.tx_type == TransactionType.CREDIT:
            total_income += tx.amount
        else:
            amt = tx.net_amount or tx.amount
            cat_spend[tx.category or "Uncategorised"] += amt
            total_expense += amt

    savings = total_income - total_expense
    return {
        "period": f"{year}-{month:02d}",
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(savings, 2),
        "savings_rate_pct": round((savings / total_income * 100) if total_income else 0, 1),
        "category_breakdown": sorted(
            [{"category": c, "amount": round(a, 2)} for c, a in cat_spend.items()],
            key=lambda x: -x["amount"]
        ),
    }

@router.get("/recurring")
async def recurring_expenses(user_id: int, days: int = 90, db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(Transaction).where(Transaction.user_id == user_id,
                                     Transaction.tx_date >= since,
                                     Transaction.tx_type == TransactionType.DEBIT)
    result = await db.execute(stmt)
    txs = result.scalars().all()
    tx_dicts = [{"merchant": t.merchant or "", "category": t.category or "Uncategorised",
                 "sub_category": t.sub_category or "", "amount": t.amount,
                 "tx_type": t.tx_type.value, "tx_date": t.tx_date,
                 "raw_text": t.raw_sms or ""} for t in txs]
    candidates = RecurringDetector().detect(tx_dicts)
    return {"recurring_count": len(candidates), "recurring_expenses": [
        {"merchant": c.merchant, "category": c.category, "amount": c.amount,
         "frequency": c.frequency, "occurrences": c.occurrences,
         "next_expected": c.next_expected.isoformat() if c.next_expected else None,
         "confidence": c.confidence} for c in candidates
    ]}

@router.get("/top-merchants")
async def top_merchants(user_id: int, days: int = 30, top_n: int = 10, db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(Transaction).where(Transaction.user_id == user_id,
                                     Transaction.tx_date >= since,
                                     Transaction.tx_type == TransactionType.DEBIT)
    result = await db.execute(stmt)
    txs = result.scalars().all()
    spend: dict = defaultdict(float)
    for tx in txs:
        if tx.merchant:
            spend[tx.merchant] += tx.net_amount or tx.amount
    top = sorted(spend.items(), key=lambda x: -x[1])[:top_n]
    return {"top_merchants": [{"merchant": m, "total_spend": round(s, 2)} for m, s in top]}

@router.get("/festival-context")
async def festival_context(db=None):
    """Returns current festival context for insight framing."""
    from app.utils.patterns import get_active_festival
    festival = get_active_festival()
    return {
        "is_festival_period": festival is not None,
        "festival": festival,
        "message": f"🎉 It's {festival['name']} season! Spending may be higher than usual." if festival else None,
    }

@router.get("/cashback-savings")
async def cashback_savings(
    user_id: int, days: int = 30, db: AsyncSession = Depends(get_db)
):
    """Returns total cashback saved this period."""
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.tx_date >= since,
        Transaction.is_cashback == True,
    )
    result = await db.execute(stmt)
    txs = result.scalars().all()
    total = sum(t.amount for t in txs)
    return {
        "total_cashback_saved": round(total, 2),
        "count": len(txs),
        "message": f"You saved ₹{total:.0f} in cashbacks this month 💰" if total > 0 else "No cashbacks detected yet.",
    }

@router.get("/wallet-floats")
async def wallet_floats(user_id: int, db: AsyncSession = Depends(get_db)):
    """Returns unreconciled wallet float balances."""
    from app.models.split import WalletFloat
    from sqlalchemy import select
    stmt = select(WalletFloat).where(
        WalletFloat.user_id == user_id,
        WalletFloat.is_reconciled == False,
    )
    result = await db.execute(stmt)
    floats = result.scalars().all()
    return {
        "unreconciled_wallets": [
            {
                "wallet": f.wallet_name,
                "loaded": f.loaded_amount,
                "remaining": f.remaining_float,
                "message": f"You loaded ₹{f.loaded_amount:.0f} into {f.wallet_name}. Where did it go?",
            }
            for f in floats
        ]
    }