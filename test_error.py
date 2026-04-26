import asyncio
from app.services.transaction_service import TransactionService
from app.utils.db import AsyncSessionLocal

async def run():
    db = AsyncSessionLocal()
    svc = TransactionService(db, user_id=1)
    try:
        await svc.process_sms('Rs.400 credited to A/c XX1234. VPA swiggy@icici. Date 30/04/2026')
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(run())
