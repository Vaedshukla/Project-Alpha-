from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.responses import success
from app.core.database import get_db
from app.core.security import require_roles, Role
from app.services.analytics_service import daily_summary, device_summary


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily", dependencies=[Depends(require_roles(Role.admin))])
async def daily_report(db: AsyncSession = Depends(get_db)):
    data = await daily_summary(db)
    return success("ok", data)


@router.get("/device/{device_id}", dependencies=[Depends(require_roles(Role.admin))])
async def device_report(device_id: str, db: AsyncSession = Depends(get_db)):
    data = await device_summary(db, device_id)
    return success("ok", data)

