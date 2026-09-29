"""Auth router — login + public sign-up endpoints with rate limiting."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.auth.auth import create_access_token, verify_password
from app.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import LoginRequest, TokenResponse, UserCreate, UserOut
from app.auth.auth import hash_password, require_role

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(f"{settings.login_rate_limit}/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return a JWT access token."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Same error for wrong email or wrong password (prevent enumeration)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token, expires_in = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/signup", response_model=UserOut, status_code=201)
@limiter.limit("3/minute")
async def public_signup(
    request: Request,
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Public self-registration — always creates a CITIZEN account."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=UserRole.CITIZEN,  # Public signups are always CITIZEN
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/register", response_model=UserOut, status_code=201)
async def register_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    """Admin-only: create a new user account with any role."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    if body.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=UserRole(body.role),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
