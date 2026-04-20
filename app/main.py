from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sms, transactions, feedback, splits, insights, review, users
from app.utils.db import create_all_tables
from config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()   # creates all DB tables on startup
    yield

app = FastAPI(
    title=settings.app_name,
    description="AI-based Auto Categorisation & Spending Pattern Detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router,        prefix="/api/users",        tags=["Users"])
app.include_router(sms.router,          prefix="/api/sms",          tags=["SMS Ingestion"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(feedback.router,     prefix="/api/feedback",     tags=["Feedback"])
app.include_router(splits.router,       prefix="/api/splits",       tags=["Splits"])
app.include_router(insights.router,     prefix="/api/insights",     tags=["Insights"])
app.include_router(review.router,       prefix="/api/review",       tags=["Review Queue"])

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}