from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.transaction import Transaction, ReviewStatus
from app.utils.db import get_db
from config.settings import settings

router = APIRouter()

class ReviewApprovalRequest(BaseModel):
    user_id: int
    transaction_id: int
    category: str
    sub_category: str = "General"

@router.get("/queue")
async def get_review_queue(user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Transaction).where(Transaction.user_id == user_id,
                                     Transaction.review_status == ReviewStatus.PENDING
                                     ).order_by(Transaction.tx_date.desc())
    result = await db.execute(stmt)
    txs = result.scalars().all()
    return {"pending_count": len(txs), "transactions": [t.to_output_dict() for t in txs]}

@router.post("/approve")
async def approve_review(req: ReviewApprovalRequest, db: AsyncSession = Depends(get_db)):
    tx = await db.get(Transaction, req.transaction_id)
    if not tx or tx.user_id != req.user_id:
        return {"error": "Not found"}
    tx.category = req.category
    tx.sub_category = req.sub_category
    tx.review_status = ReviewStatus.REVIEWED
    tx.confidence = 0.99
    await db.flush()
    return {"status": "reviewed", "transaction": tx.to_output_dict()}

@router.post("/auto-assign-expired")
async def auto_assign_expired(db: AsyncSession = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=settings.review_auto_assign_days)
    stmt = select(Transaction).where(Transaction.review_status == ReviewStatus.PENDING,
                                     Transaction.created_at <= cutoff,
                                     Transaction.category != None)
    result = await db.execute(stmt)
    txs = result.scalars().all()
    for tx in txs:
        tx.review_status = ReviewStatus.AUTO_ASSIGNED
    await db.flush()
    return {"auto_assigned": len(txs)}