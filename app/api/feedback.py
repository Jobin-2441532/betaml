from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.learning_service import LearningService
from app.services.transaction_service import TransactionService
from app.utils.db import get_db

router = APIRouter()

class CorrectionRequest(BaseModel):
    user_id: int
    transaction_id: int
    category: str
    sub_category: str = "General"

@router.post("/correct")
async def correct_category(req: CorrectionRequest, db: AsyncSession = Depends(get_db)):
    service = TransactionService(db=db, user_id=req.user_id)
    result = await service.correct_category(req.transaction_id, req.category, req.sub_category)
    return {"status": "updated", "transaction": result}

@router.get("/stats")
async def feedback_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    return await LearningService(db).get_feedback_stats(user_id)

@router.get("/merchant-mappings")
async def merchant_mappings(user_id: int, db: AsyncSession = Depends(get_db)):
    mappings = await LearningService(db).get_merchant_mappings(user_id)
    return {"count": len(mappings), "mappings": [
        {"merchant": k, "category": v[0], "sub_category": v[1]} for k, v in mappings.items()
    ]}