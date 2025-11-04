import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.responses import success
from app.core.database import get_db
from app.core.security import require_roles, Role
from app.models.activity_log import ActivityLog
from app.models.admin_action import AdminAction


router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/logs", dependencies=[Depends(require_roles(Role.admin))])
async def get_logs(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * size
    total = (await db.execute(select(func.count()).select_from(ActivityLog))).scalar() or 0
    result = await db.execute(select(ActivityLog).order_by(ActivityLog.timestamp.desc()).offset(offset).limit(size))
    items = [
        {
            "id": str(a.id),
            "user_id": str(a.user_id) if a.user_id else None,
            "device_id": str(a.device_id) if a.device_id else None,
            "action_type": a.action_type,
            "details": a.details,
            "timestamp": a.timestamp,
        }
        for a in result.scalars().all()
    ]
    return success("ok", {"items": items, "total": int(total)})


@router.post("/admin/actions", dependencies=[Depends(require_roles(Role.admin))])
async def create_admin_action(action: str, target_type: str, target_id: str | None = None, notes: str | None = None, db: AsyncSession = Depends(get_db), claims=Depends(require_roles(Role.admin))):
    admin_id = uuid.UUID(claims.get("sub")) if claims.get("sub") else None
    entry = AdminAction(id=uuid.uuid4(), admin_id=admin_id, action=action, target_type=target_type, target_id=uuid.UUID(target_id) if target_id else None, notes=notes)
    db.add(entry)
    await db.commit()
    return success("recorded", {"id": str(entry.id)})

