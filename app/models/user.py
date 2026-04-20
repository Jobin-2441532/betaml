from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.db import Base

class UserType(str, enum.Enum):
    STUDENT = "student"; WORKING = "working"
    FREELANCER = "freelancer"; BUSINESS = "business"

class ShoppingBehavior(str, enum.Enum):
    ONLINE = "online"; OFFLINE = "offline"; MIXED = "mixed"

class FoodHabit(str, enum.Enum):
    COOK = "cook"; ORDER = "order"; BOTH = "both"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), default=UserType.WORKING)
    shopping_behavior: Mapped[ShoppingBehavior] = mapped_column(Enum(ShoppingBehavior), default=ShoppingBehavior.MIXED)
    food_habit: Mapped[FoodHabit] = mapped_column(Enum(FoodHabit), default=FoodHabit.BOTH)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    transactions: Mapped[list] = relationship("Transaction", back_populates="user")
    merchant_mappings: Mapped[list] = relationship("MerchantMapping", back_populates="user")