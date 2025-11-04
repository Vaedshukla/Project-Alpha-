from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


async def log_activity(db: AsyncSession, action_type: str, user_id: Optional[str] = None, device_id: Optional[str] = None, details: Optional[dict[str, Any]] = None) -> None:
    entry = ActivityLog(action_type=action_type, user_id=user_id, device_id=device_id, details=details or {})
    db.add(entry)
    await db.flush()

