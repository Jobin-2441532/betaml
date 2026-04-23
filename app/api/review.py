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
    This counts as a learning correction — saves merchant mapping.
    """
    tx = await db.get(Transaction, req.transaction_id)
    if not tx or tx.user_id != req.user_id:
        return {"error": "Transaction not found"}

    original_category = tx.category or "Uncategorised"

    # Update transaction
    tx.category = req.category
    tx.sub_category = req.sub_category
    tx.review_status = ReviewStatus.REVIEWED
    tx.confidence = 0.99

    # ── Count this as a learning correction ──────────────────────────────────
    from app.models.learning import FeedbackLog, MerchantMapping
    from datetime import datetime

    # Log the feedback
    log = FeedbackLog(
        user_id=req.user_id,
        transaction_id=req.transaction_id,
        original_category=original_category,
        corrected_category=req.category,
        original_confidence=tx.confidence or 0.0,
        created_at=datetime.utcnow(),
    )
    db.add(log)

    # Save merchant mapping so AI learns
    if tx.merchant:
        key = tx.merchant.lower().strip()
        stmt = select(MerchantMapping).where(
            MerchantMapping.user_id == req.user_id,
            MerchantMapping.merchant_key == key,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.category = req.category
            existing.sub_category = req.sub_category
            existing.usage_count += 1
            existing.updated_at = datetime.utcnow()
        else:
            db.add(MerchantMapping(
                user_id=req.user_id,
                merchant_key=key,
                category=req.category,
                sub_category=req.sub_category,
                confidence_override=0.99,
                usage_count=1,
            ))

    await db.flush()
    return {"status": "reviewed", "transaction": tx.to_output_dict()}


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