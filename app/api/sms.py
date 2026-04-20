from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.transaction_service import TransactionService
from app.utils.db import get_db

router = APIRouter()

class SMSRequest(BaseModel):
    user_id: int
    sms_text: str
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    location_label: Optional[str] = None

class BulkSMSRequest(BaseModel):
    user_id: int
    sms_list: list[str]

@router.post("/ingest")
async def ingest_sms(req: SMSRequest, db: AsyncSession = Depends(get_db)):
    service = TransactionService(db=db, user_id=req.user_id)
    result = await service.process_sms(
        req.sms_text, req.location_lat, req.location_lon, req.location_label
    )
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result

@router.post("/bulk-ingest")
async def bulk_ingest(req: BulkSMSRequest, db: AsyncSession = Depends(get_db)):
    service = TransactionService(db=db, user_id=req.user_id)
    results = []
    for sms in req.sms_list:
        try:
            results.append({"status": "ok", "data": await service.process_sms(sms)})
        except Exception as e:
            results.append({"status": "error", "sms": sms[:80], "detail": str(e)})
    return {"processed": len(results), "results": results}