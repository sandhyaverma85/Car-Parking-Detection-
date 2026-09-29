"""
Authentication utilities — JWT + Argon2 password hashing + RBAC dependencies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.models import User, UserRole

settings = get_settings()

# Argon2 via passlib
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
_bearer = HTTPBearer(auto_error=True)


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plain-text password with Argon2."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its Argon2 hash."""
    return _pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    """
    Create a signed JWT access token.

    Returns:
        (token_string, expires_in_seconds)
    """
    expire_seconds = settings.jwt_access_token_expire_minutes * 60
    exp = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": exp,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expire_seconds


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI Dependencies ───────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: validate JWT and return the current user from DB."""
    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_role(*roles: UserRole):
    """
    Dependency factory: require one of the specified roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return _check
