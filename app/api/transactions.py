from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionType, ReviewStatus
from app.utils.db import get_db

router = APIRouter()


# ── List transactions ─────────────────────────────────────────────────────────
@router.get("/")
async def list_transactions(
    user_id: int,
    category: Optional[str] = None,
    tx_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    is_recurring: Optional[bool] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    conditions = [Transaction.user_id == user_id]
    if category:
        conditions.append(Transaction.category == category)
    if tx_type:
        conditions.append(Transaction.tx_type == TransactionType(tx_type))
    if from_date:
        conditions.append(Transaction.tx_date >= from_date)
    if to_date:
        conditions.append(Transaction.tx_date <= to_date)
    if is_recurring is not None:
        conditions.append(Transaction.is_recurring == is_recurring)

    stmt = (
        select(Transaction)
        .where(and_(*conditions))
        .order_by(Transaction.tx_date.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    txs = result.scalars().all()
    return {"count": len(txs), "transactions": [t.to_output_dict() for t in txs]}


# ── Payment method breakdown ──────────────────────────────────────────────────
# IMPORTANT: This MUST be above /{transaction_id} to avoid route conflict
@router.get("/payment-method-breakdown")
async def payment_method_breakdown(
    user_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.tx_date >= since,
        Transaction.tx_type == TransactionType.DEBIT,
    )
    result = await db.execute(stmt)
    txs = result.scalars().all()

    breakdown: dict = defaultdict(float)
    for tx in txs:
        method = tx.payment_method or "UNKNOWN"
        breakdown[method] += tx.net_amount or tx.amount

    return {
        "period_days": days,
        "breakdown": [
            {"method": k, "amount": round(v, 2)}
            for k, v in sorted(breakdown.items(), key=lambda x: -x[1])
        ],
    }


# ── Get single transaction ────────────────────────────────────────────────────
@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    tx = await db.get(Transaction, transaction_id)
    if not tx or tx.user_id != user_id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx.to_output_dict()


# ── Delete transaction ────────────────────────────────────────────────────────
@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    tx = await db.get(Transaction, transaction_id)
    if not tx or tx.user_id != user_id:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(tx)
    return {"deleted": True, "id": transaction_id}


# ── Pydantic models ───────────────────────────────────────────────────────────
class P2PReviewRequest(BaseModel):
    user_id: int
    transaction_id: int
    context: str


class BasketSplitItem(BaseModel):
    category: str
    amount: float


class BasketSplitRequest(BaseModel):
    user_id: int
    transaction_id: int
    splits: list[BasketSplitItem]


class FamilyTagRequest(BaseModel):
    user_id: int
    transaction_id: int
    is_family: bool = True


class SubscriptionReviewRequest(BaseModel):
    user_id: int
    transaction_id: int
    subscription_type: str
    member_count: int = 1


# ── P2P review ────────────────────────────────────────────────────────────────
@router.post("/p2p-review")
async def p2p_review(
    req: P2PReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    tx = await db.get(Transaction, req.transaction_id)
    if not tx or tx.user_id != req.user_id:
        raise HTTPException(404, "Not found")

    context_map = {
        "food":          ("Food & Dining",      "P2P Food"),
        "travel":        ("Transport",           "P2P Travel"),
        "entertainment": ("Entertainment",       "P2P Entertainment"),
        "gift":          ("Personal Transfer",   "Gift Received"),
        "reimbursement": ("Personal Transfer",   "Reimbursement"),
        "income":        ("Income",              "P2P Income"),
        "others":        ("Uncategorised",       "P2P Other"),
    }
    cat, sub = context_map.get(req.context, ("Uncategorised", "P2P"))

    tx.category = cat
    tx.sub_category = sub
    tx.p2p_reviewed = True
    tx.p2p_context = req.context
    tx.review_status = ReviewStatus.REVIEWED
    tx.confidence = 0.99
    await db.flush()
    return {"status": "updated", "transaction": tx.to_output_dict()}


# ── Basket split ──────────────────────────────────────────────────────────────
@router.post("/basket-split")
async def basket_split(
    req: BasketSplitRequest,
    db: AsyncSession = Depends(get_db),
):
    tx = await db.get(Transaction, req.transaction_id)
    if not tx or tx.user_id != req.user_id:
        raise HTTPException(404, "Not found")

    total = sum(s.amount for s in req.splits)
    if abs(total - tx.amount) > 1:
        raise HTTPException(
            400,
            f"Split amounts ({total}) don't match transaction ({tx.amount})",
        )

    tx.basket_splits = json.dumps([s.dict() for s in req.splits])
    tx.is_mixed_basket = False
    tx.review_status = ReviewStatus.REVIEWED
    primary = max(req.splits, key=lambda s: s.amount)
    tx.category = primary.category
    await db.flush()
    return {"status": "split_saved", "transaction": tx.to_output_dict()}


# ── Family tag ────────────────────────────────────────────────────────────────
@router.post("/family-tag")
async def family_tag(
    req: FamilyTagRequest,
    db: AsyncSession = Depends(get_db),
):
    tx = await db.get(Transaction, req.transaction_id)
    if not tx or tx.user_id != req.user_id:
        raise HTTPException(404, "Not found")

    tx.is_family_expense = req.is_family
    if req.is_family:
        existing_tags = tx.tags.split(",") if tx.tags else []
        if "family" not in existing_tags:
            existing_tags.append("family")
        tx.tags = ",".join(existing_tags)
    await db.flush()
    return {"status": "updated", "transaction": tx.to_output_dict()}


# ── Subscription review ───────────────────────────────────────────────────────
@router.post("/subscription-review")
async def subscription_review(
    req: SubscriptionReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    tx = await db.get(Transaction, req.transaction_id)
    if not tx or tx.user_id != req.user_id:
        raise HTTPException(404, "Not found")

    tx.subscription_type = req.subscription_type
    tx.subscription_members = req.member_count
    if req.subscription_type == "group" and req.member_count > 1:
        tx.net_amount = round(tx.amount / req.member_count, 2)
    tx.review_status = ReviewStatus.REVIEWED
    await db.flush()
    return {"status": "updated", "transaction": tx.to_output_dict()}