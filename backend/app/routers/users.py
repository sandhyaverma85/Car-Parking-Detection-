"""Users router — admin only user management."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_user, require_role
from app.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import UserOut

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return user


@router.get("/", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(UserRole.ADMIN)),
):
    """Admin: list all users."""
    result = await db.execute(select(User))
    return result.scalars().all()


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Admin: deactivate a user account (soft delete)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
