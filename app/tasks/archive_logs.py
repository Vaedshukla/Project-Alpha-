from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.browsing_history import BrowsingHistory
from app.models.activity_log import ActivityLog


async def archive_logs(retention_days: int = 30):
    """
    Archive logs older than retention_days.
    In production, this would move to cloud storage or archived_logs table.
    For MVP, we'll mark them as archived or delete (based on policy).
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    async with AsyncSessionLocal() as db:
        # Get old browsing history
        bh_result = await db.execute(
            select(BrowsingHistory).where(BrowsingHistory.timestamp < cutoff_date)
        )
        old_bh = bh_result.scalars().all()
        
        # Get old activity logs
        al_result = await db.execute(
            select(ActivityLog).where(ActivityLog.timestamp < cutoff_date)
        )
        old_al = al_result.scalars().all()
        
        # For MVP: delete old logs (in production, move to archive table/storage)
        archived_count = 0
        for log in old_bh:
            await db.delete(log)
            archived_count += 1
        
        for log in old_al:
            await db.delete(log)
            archived_count += 1
        
        await db.commit()
        return archived_count


if __name__ == "__main__":
    import asyncio
    retention = getattr(settings, "log_retention_days", 30)
    count = asyncio.run(archive_logs(retention))
    print(f"Archived {count} logs")

