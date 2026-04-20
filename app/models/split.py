from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column
from app.utils.db import Base

class SplitStatus(str, enum.Enum):
    OPEN = "open"; PARTIAL = "partial"; SETTLED = "settled"

class SplitGroup(Base):
    __tablename__ = "split_groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    anchor_tx_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"))
    total_debit: Mapped[float] = mapped_column(Float)
    total_credited_back: Mapped[float] = mapped_column(Float, default=0.0)
    net_expense: Mapped[float] = mapped_column(Float)
    status: Mapped[SplitStatus] = mapped_column(Enum(SplitStatus), default=SplitStatus.OPEN)
    member_count: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    merchant: Mapped[str] = mapped_column(String(256))
    category: Mapped[str] = mapped_column(String(64))
    sub_category: Mapped[Optional[str]] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(Float)
    frequency: Mapped[str] = mapped_column(String(32))
    last_seen: Mapped[datetime] = mapped_column(DateTime)
    next_expected: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class WalletFloat(Base):
    __tablename__ = "wallet_floats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    wallet_name: Mapped[str] = mapped_column(String(64))   # "Paytm" | "PhonePe" | "Amazon Pay"
    loaded_amount: Mapped[float] = mapped_column(Float)
    spent_amount: Mapped[float] = mapped_column(Float, default=0.0)
    remaining_float: Mapped[float] = mapped_column(Float)
    load_tx_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"))
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SocialContact(Base):
    """Remembers VPAs that belong to known contacts for split detection."""
    __tablename__ = "social_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    vpa: Mapped[str] = mapped_column(String(256), index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(128))
    is_family: Mapped[bool] = mapped_column(Boolean, default=False)
    split_count: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())