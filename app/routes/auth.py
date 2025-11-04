import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password, Role
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenPair, RefreshRequest
from app.utils.responses import success


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    role = UserRole(payload.role) if payload.role in {r.value for r in UserRole} else UserRole.student
    user = User(id=uuid.uuid4(), name=payload.name, email=payload.email, password_hash=hash_password(payload.password), role=role)
    db.add(user)
    await db.commit()
    claims = {"role": user.role.value}
    tokens = TokenPair(
        access_token=create_access_token(str(user.id), role=user.role.value, extra_claims=claims),
        refresh_token=create_refresh_token(str(user.id), role=user.role.value, extra_claims=claims),
    )
    return success("registered", tokens.model_dump())


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    claims = {"role": user.role.value}
    tokens = TokenPair(
        access_token=create_access_token(str(user.id), role=user.role.value, extra_claims=claims),
        refresh_token=create_refresh_token(str(user.id), role=user.role.value, extra_claims=claims),
    )
    return success("login ok", tokens.model_dump())


@router.post("/refresh")
async def refresh(payload: RefreshRequest):
    from app.core.security import decode_token

    claims = decode_token(payload.refresh_token)
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    user_id = claims.get("sub")
    role = claims.get("role")
    access = create_access_token(user_id, role=role, extra_claims={"role": role})
    return success("refreshed", {"access_token": access, "token_type": "bearer"})

