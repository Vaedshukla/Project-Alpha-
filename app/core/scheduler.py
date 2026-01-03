from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.tasks import anonymize
from app.tasks import archive_logs
from app.services.behavior_ai import update_ai_insights
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select


scheduler = AsyncIOScheduler()


async def refresh_ai_insights_job():
    """Daily job to refresh AI insights for all users."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        for user in users:
            try:
                await update_ai_insights(str(user.id), db)
            except Exception as e:
                print(f"Error updating insights for user {user.id}: {e}")


async def archive_logs_job():
    """Weekly job to archive old logs."""
    retention = settings.log_retention_days
    count = await archive_logs.archive_logs(retention)
    print(f"Archived {count} logs")


async def anonymize_logs_job():
    """Weekly job to anonymize old logs."""
    retention = 90  # 90 days for anonymization
    count = await anonymize.anonymize_old_logs(retention)
    print(f"Anonymized {count} logs")


def setup_scheduler():
    """Configure and start the scheduler."""
    # Daily AI insights refresh (runs at 2 AM)
    scheduler.add_job(
        refresh_ai_insights_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="refresh_ai_insights",
        replace_existing=True
    )
    
    # Weekly log archiving (runs Sunday at 3 AM)
    scheduler.add_job(
        archive_logs_job,
        trigger=CronTrigger(day_of_week=6, hour=3, minute=0),  # Sunday
        id="archive_logs",
        replace_existing=True
    )
    
    # Weekly anonymization (runs Sunday at 4 AM)
    scheduler.add_job(
        anonymize_logs_job,
        trigger=CronTrigger(day_of_week=6, hour=4, minute=0),  # Sunday
        id="anonymize_logs",
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler."""
    scheduler.shutdown()

