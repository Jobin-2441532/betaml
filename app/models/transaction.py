from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.db import Base

class TransactionType(str, enum.Enum):
    DEBIT = "debit"; CREDIT = "credit"

class ReviewStatus(str, enum.Enum):
    PENDING = "pending"; REVIEWED = "reviewed"; AUTO_ASSIGNED = "auto_assigned"

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    raw_sms: Mapped[Optional[str]] = mapped_column(Text)
    bank: Mapped[Optional[str]] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    tx_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    tx_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    merchant: Mapped[Optional[str]] = mapped_column(String(256))
    vpa: Mapped[Optional[str]] = mapped_column(String(256))
    account_ref: Mapped[Optional[str]] = mapped_column(String(64))
    payment_method: Mapped[Optional[str]] = mapped_column(String(32))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    sub_category: Mapped[Optional[str]] = mapped_column(String(64))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    is_split: Mapped[bool] = mapped_column(Boolean, default=False)
    is_refund: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cashback: Mapped[bool] = mapped_column(Boolean, default=False)
    is_income: Mapped[bool] = mapped_column(Boolean, default=False)
    is_transfer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_wallet_load: Mapped[bool] = mapped_column(Boolean, default=False)
    # Add these NEW columns after is_wallet_load
    is_family_expense: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deposit: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cashback: Mapped[bool] = mapped_column(Boolean, default=False)
    cashback_linked_tx_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transactions.id"))
    deposit_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_type: Mapped[Optional[str]] = mapped_column(String(32))  # "personal" | "group"
    subscription_members: Mapped[Optional[int]] = mapped_column(Integer)
    is_mixed_basket: Mapped[bool] = mapped_column(Boolean, default=False)
    basket_splits: Mapped[Optional[str]] = mapped_column(Text)  # JSON: [{"category":"Groceries","amount":1400}]
    p2p_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    p2p_context: Mapped[Optional[str]] = mapped_column(String(64))  # "food"|"travel"|"entertainment"|"gift"|"reimbursement"|"income"
    net_amount: Mapped[Optional[float]] = mapped_column(Float)
    tags: Mapped[Optional[str]] = mapped_column(String(512))
    original_tx_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transactions.id"))
    review_status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    location_lat: Mapped[Optional[float]] = mapped_column(Float)
    location_lon: Mapped[Optional[float]] = mapped_column(Float)
    location_label: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship("User", back_populates="transactions")

    def to_output_dict(self) -> dict:
        import json
        return {
        "id": self.id,
        "amount": self.amount,
        "type": self.tx_type.value,
        "category": self.category,
        "sub_category": self.sub_category,
        "confidence": round(self.confidence or 0, 4),
        "merchant": self.merchant,
        "vpa": self.vpa,
        "is_recurring": self.is_recurring,
        "is_split": self.is_split,
        "is_refund": self.is_refund,
        "is_cashback": self.is_cashback,
        "is_income": self.is_income,
        "is_transfer": self.is_transfer,
        "is_wallet_load": self.is_wallet_load,
        "is_family_expense": self.is_family_expense,
        "is_deposit": self.is_deposit,
        "is_mixed_basket": self.is_mixed_basket,
        "p2p_reviewed": self.p2p_reviewed,
        "p2p_context": self.p2p_context,
        "subscription_type": self.subscription_type,
        "subscription_members": self.subscription_members,
        "basket_splits": json.loads(self.basket_splits) if self.basket_splits else [],
        "net_amount": self.net_amount if self.net_amount is not None else self.amount,
        "original_tx_id": self.original_tx_id,
        "has_refund_applied": (self.net_amount is not None and self.amount > self.net_amount) if self.tx_type.value == "debit" else False,
        "tags": self.tags.split(",") if self.tags else [],
        "explanation": self.explanation,
        "payment_method": self.payment_method,
        "tx_date": self.tx_date.isoformat() if self.tx_date else None,
        "review_status": self.review_status.value,
        "raw_sms": self.raw_sms,
    }