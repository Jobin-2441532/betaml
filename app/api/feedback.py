import os
import subprocess
import sys
from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import FeedbackLog, MerchantMapping
from app.models.transaction import Transaction, ReviewStatus
from app.utils.db import get_db

router = APIRouter()

RETRAIN_THRESHOLD = 5  # Changed from 10 to 5


class CorrectionRequest(BaseModel):
    user_id: int
    transaction_id: int
    category: str
    sub_category: str = "General"
    is_reimbursement: bool = False


@router.post("/correct")
async def correct_category(
    req: CorrectionRequest, db: AsyncSession = Depends(get_db)
):
    from app.services.learning_service import LearningService
    from app.services.transaction_service import TransactionService

    service = TransactionService(db=db, user_id=req.user_id)
    result = await service.correct_category(
        req.transaction_id, req.category, req.sub_category, req.is_reimbursement
    )
    return {"status": "updated", "transaction": result}


@router.get("/stats")
async def feedback_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    from app.services.learning_service import LearningService
    return await LearningService(db).get_feedback_stats(user_id)


@router.get("/merchant-mappings")
async def merchant_mappings(user_id: int, db: AsyncSession = Depends(get_db)):
    from app.services.learning_service import LearningService
    mappings = await LearningService(db).get_merchant_mappings(user_id)
    return {
        "count": len(mappings),
        "mappings": [
            {"merchant": k, "category": v[0], "sub_category": v[1]}
            for k, v in mappings.items()
        ],
    }


@router.get("/learning-stats")
async def learning_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    """Shows how much the AI has learned from this user."""

    mapping_count = await db.scalar(
        select(func.count(MerchantMapping.id)).where(
            MerchantMapping.user_id == user_id
        )
    ) or 0

    correction_count = await db.scalar(
        select(func.count(FeedbackLog.id)).where(
            FeedbackLog.user_id == user_id
        )
    ) or 0

    stmt = select(FeedbackLog).where(FeedbackLog.user_id == user_id)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    corrections_by_cat = Counter(l.original_category for l in logs)

    ready = correction_count >= RETRAIN_THRESHOLD
    remaining = max(0, RETRAIN_THRESHOLD - correction_count)

    return {
        "merchant_mappings_learned": mapping_count,
        "total_corrections_made": correction_count,
        "most_corrected_categories": corrections_by_cat.most_common(5),
        "model_will_improve_after": remaining,
        "ready_to_retrain": ready,
        "retrain_threshold": RETRAIN_THRESHOLD,
        "message": (
            f"AI has learned {mapping_count} merchant patterns from you. "
            f"{'Ready to retrain! Click the button below.' if ready else f'Make {remaining} more corrections to improve the model.'}"
        ),
    }


@router.post("/retrain-model")
async def retrain_model():
    """Retrain the ML model using all user corrections."""
    import subprocess
    import sys
    import os

    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        script_path = os.path.join(project_root, "scripts", "train_model.py")

        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            cwd=project_root,
            timeout=120,
            # Fix Windows encoding issue
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Model retrained successfully with your corrections",
                "output": result.stdout[-800:] if result.stdout else "",
            }
        else:
            return {
                "status": "error",
                "message": "Retraining script failed",
                "error": result.stderr[-500:] if result.stderr else "",
                "stdout": result.stdout[-300:] if result.stdout else "",
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Training timed out after 2 minutes"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/backfill-mappings")
async def backfill_mappings(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Backfill merchant mappings from existing feedback logs.
    Run once to fix historical corrections that had no merchant.
    """
    from app.models.transaction import Transaction
    from datetime import datetime

    stmt = select(FeedbackLog).where(FeedbackLog.user_id == user_id)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    saved = 0
    for log in logs:
        tx = await db.get(Transaction, log.transaction_id)
        if not tx:
            continue

        # Determine key
        merchant_key = None
        if tx.merchant and tx.merchant.lower() not in ("unknown", ""):
            merchant_key = tx.merchant
        elif tx.vpa:
            merchant_key = tx.vpa.split("@")[0]

        if not merchant_key:
            continue

        key = merchant_key.lower().strip()

        # Check if mapping already exists
        stmt2 = select(MerchantMapping).where(
            MerchantMapping.user_id == user_id,
            MerchantMapping.merchant_key == key,
        )
        res2 = await db.execute(stmt2)
        existing = res2.scalar_one_or_none()

        if not existing:
            db.add(MerchantMapping(
                user_id=user_id,
                merchant_key=key,
                category=log.corrected_category,
                sub_category="General",
                confidence_override=0.99,
                usage_count=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))
            saved += 1

    await db.flush()
    return {"backfilled": saved, "total_logs": len(logs)}