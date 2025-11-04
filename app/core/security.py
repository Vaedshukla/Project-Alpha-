from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

from bcrypt import gensalt, hashpw, checkpw
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db


class Role(str, Enum):
    admin = "admin"
    parent = "parent"
    student = "student"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def hash_password(plain_password: str) -> str:
    return hashpw(plain_password.encode("utf-8"), gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(subject: str, expires_delta: timedelta, token_type: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: Optional[str] = None, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    claims = dict(extra_claims or {})
    if role:
        claims["role"] = role
    return create_token(subject, timedelta(minutes=settings.jwt_access_expires_minutes), "access", claims)


def create_refresh_token(subject: str, role: Optional[str] = None, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    claims = dict(extra_claims or {})
    if role:
        claims["role"] = role
    return create_token(subject, timedelta(days=settings.jwt_refresh_expires_days), "refresh", claims)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    return decode_token(token)


def require_roles(*roles: Role):
    def dependency(claims: Dict[str, Any] = Depends(get_current_user_claims)) -> Dict[str, Any]:
        role: Optional[str] = claims.get("role")
        if roles and role not in [r.value for r in roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims

    return dependency


async def get_current_user(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User  # local import to avoid circular

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

