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
    """
    Returns transactions that need review:
    - Low confidence (below show threshold)
    - Uncategorised
    - Mixed basket
    - P2P unreviewed
    """
    stmt = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.review_status == ReviewStatus.PENDING,
        )
        .order_by(Transaction.tx_date.desc())
    )
    result = await db.execute(stmt)
    txs = result.scalars().all()

    return {
        "pending_count": len(txs),
        "transactions": [t.to_output_dict() for t in txs],
    }


@router.post("/approve")
async def approve_review(
    req: ReviewApprovalRequest, db: AsyncSession = Depends(get_db)
):
    """
    User confirms/corrects a transaction from review queue.
    Delegates to LearningService so the same rich learning logic is used
    as when correcting from the Transaction History page.
    """
    from app.services.learning_service import LearningService

    tx = await db.get(Transaction, req.transaction_id)
    if not tx or tx.user_id != req.user_id:
        return {"error": "Transaction not found"}

    sub_category = req.sub_category or "General"

    # ── Delegate to LearningService for rich merchant-key extraction ──────────
    # This saves: merchant name, VPA prefix, AND raw SMS keywords (Netflix etc.)
    learning = LearningService(db)
    await learning.record_correction(
        user_id=req.user_id,
        transaction_id=req.transaction_id,
        corrected_category=req.category,
        corrected_sub_category=sub_category,
    )

    # mark as reviewed (record_correction already sets confidence=0.99 & commits)
    tx = await db.get(Transaction, req.transaction_id)
    if tx:
        tx.review_status = ReviewStatus.REVIEWED
        await db.commit()

    return {"status": "reviewed", "transaction": tx.to_output_dict() if tx else {}}


@router.post("/auto-assign-expired")
async def auto_assign_expired(db: AsyncSession = Depends(get_db)):
    """Auto-assign after 7 days in queue."""
    cutoff = datetime.utcnow() - timedelta(days=settings.review_auto_assign_days)
    stmt = select(Transaction).where(
        Transaction.review_status == ReviewStatus.PENDING,
        Transaction.created_at <= cutoff,
        Transaction.category != None,
    )
    result = await db.execute(stmt)
    txs = result.scalars().all()
    count = 0
    for tx in txs:
        tx.review_status = ReviewStatus.AUTO_ASSIGNED
        count += 1
    await db.flush()
    return {"auto_assigned": count}