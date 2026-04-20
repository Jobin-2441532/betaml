from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.split_engine import RawTransaction, SplitEngine
from app.models.transaction import Transaction
from app.utils.db import get_db

router = APIRouter()

@router.get("/detect")
async def detect_splits(user_id: int, days: int = 30, db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(Transaction).where(Transaction.user_id == user_id, Transaction.tx_date >= since)
    result = await db.execute(stmt)
    txs = result.scalars().all()

    raw_txs = [RawTransaction(id=t.id, amount=t.amount, tx_type=t.tx_type.value,
                               tx_date=t.tx_date, merchant=t.merchant, vpa=t.vpa)
               for t in txs]

    splits = SplitEngine().detect_splits(raw_txs)
    return {"splits_found": len(splits), "split_groups": [
        {"anchor_tx_id": s.anchor_tx_id, "credit_tx_ids": s.credit_tx_ids,
         "total_debit": s.total_debit, "total_credited_back": s.total_credited,
         "net_expense": s.net_expense, "member_count": s.member_count,
         "status": s.status, "confidence": s.confidence, "explanation": s.explanation}
        for s in splits
    ]}