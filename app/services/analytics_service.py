from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.browsing_history import BrowsingHistory
from app.models.activity_log import ActivityLog


async def daily_summary(db: AsyncSession) -> Dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=1)
    visits_q = await db.execute(select(func.count()).select_from(BrowsingHistory).where(BrowsingHistory.timestamp >= since))
    blocked_q = await db.execute(select(func.count()).select_from(ActivityLog).where(ActivityLog.action_type == "blocked", ActivityLog.timestamp >= since))
    return {"visits": int(visits_q.scalar() or 0), "blocked": int(blocked_q.scalar() or 0)}


async def device_summary(db: AsyncSession, device_id: str) -> Dict[str, Any]:
    visits_q = await db.execute(select(func.count()).select_from(BrowsingHistory).where(BrowsingHistory.device_id == device_id))
    blocked_q = await db.execute(select(func.count()).select_from(ActivityLog).where(ActivityLog.device_id == device_id, ActivityLog.action_type == "blocked"))
    return {"device_id": str(device_id), "visits": int(visits_q.scalar() or 0), "blocked": int(blocked_q.scalar() or 0)}

