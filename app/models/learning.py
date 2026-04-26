from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.db import Base

class MerchantMapping(Base):
    __tablename__ = "merchant_mappings"
    __table_args__ = (
        # ✅ FIX: Prevent duplicate (user_id, merchant_key) pairs
        UniqueConstraint("user_id", "merchant_key", name="uq_user_merchant"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    merchant_key: Mapped[str] = mapped_column(String(256), index=True)
    category: Mapped[str] = mapped_column(String(64))
    sub_category: Mapped[str] = mapped_column(String(64))
    confidence_override: Mapped[float] = mapped_column(Float, default=1.0)
    usage_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship("User", back_populates="merchant_mappings")

class FeedbackLog(Base):
    __tablename__ = "feedback_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), index=True)
    original_category: Mapped[str] = mapped_column(String(64))
    corrected_category: Mapped[str] = mapped_column(String(64))
    original_confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class UserSalaryProfile(Base):
    __tablename__ = "user_salary_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, unique=True)
    expected_amount_min: Mapped[float] = mapped_column(Float)
    expected_amount_max: Mapped[float] = mapped_column(Float)
    employer_vpa: Mapped[str] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())