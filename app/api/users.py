import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserType, ShoppingBehavior, FoodHabit
from app.utils.db import get_db

router = APIRouter()

class UserCreateRequest(BaseModel):
    email: str
    phone: str
    password: str
    user_type: UserType = UserType.WORKING
    shopping_behavior: ShoppingBehavior = ShoppingBehavior.MIXED
    food_habit: FoodHabit = FoodHabit.BOTH

@router.post("/register", status_code=201)
async def register_user(req: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == req.email)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=req.email, phone=req.phone,
        hashed_password=hashlib.sha256(req.password.encode()).hexdigest(),
        user_type=req.user_type, shopping_behavior=req.shopping_behavior,
        food_habit=req.food_habit,
    )
    db.add(user)
    await db.flush()
    return {"id": user.id, "email": user.email, "user_type": user.user_type.value}

@router.get("/{user_id}/profile")
async def get_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    return {"id": user.id, "email": user.email,
            "user_type": user.user_type.value,
            "shopping_behavior": user.shopping_behavior.value,
            "food_habit": user.food_habit.value}