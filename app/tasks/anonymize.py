from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.browsing_history import BrowsingHistory


async def anonymize_old_logs(retention_days: int = 90):
    """
    Anonymize browsing logs older than retention_days.
    Removes URLs, generalizes domains.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    async with AsyncSessionLocal() as db:
        # Get old logs
        result = await db.execute(
            select(BrowsingHistory)
            .where(BrowsingHistory.timestamp < cutoff_date)
            .where(BrowsingHistory.url != "ANONYMIZED")  # Skip already anonymized
        )
        logs = result.scalars().all()
        
        anonymized_count = 0
        for log in logs:
            # Anonymize: remove URL, keep only domain pattern
            domain_parts = log.domain.split(".")
            if len(domain_parts) >= 2:
                # Keep only top-level domain pattern (e.g., "example.com" -> "*.com")
                log.domain = f"*.{domain_parts[-1]}"
            log.url = "ANONYMIZED"
            anonymized_count += 1
        
        await db.commit()
        return anonymized_count


if __name__ == "__main__":
    import asyncio
    count = asyncio.run(anonymize_old_logs())
    print(f"Anonymized {count} logs")

