from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_claims, require_roles, Role
from app.models.user import User
from app.schemas.user import UserBase, UserUpdate
from app.utils.responses import success


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def me(claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, claims.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success("ok", UserBase.model_validate(user).model_dump())


@router.get("/{user_id}", dependencies=[Depends(require_roles(Role.admin))])
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success("ok", UserBase.model_validate(user).model_dump())


@router.put("/{user_id}")
async def update_user(user_id: str, payload: UserUpdate, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    if claims.get("role") != Role.admin.value and claims.get("sub") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.name is not None:
        user.name = payload.name
    if payload.is_active is not None:
        # Only admins may change activation state
        if claims.get("role") != Role.admin.value:
            raise HTTPException(status_code=403, detail="Only admins can change activation state")
        user.is_active = payload.is_active
    await db.commit()
    await db.refresh(user)
    return success("updated", UserBase.model_validate(user).model_dump())

