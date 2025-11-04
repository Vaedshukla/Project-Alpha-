import asyncio
import uuid

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models import Base
from app.models.user import User, UserRole
from app.models.blocked_site import BlockedSite, MatchType, SiteCategory


async def seed():
    async with AsyncSessionLocal() as db:
        # Admin user
        exists = (await db.execute(select(User).where(User.email == "admin@example.com"))).scalar_one_or_none()
        if not exists:
            admin = User(
                id=uuid.uuid4(),
                name="Admin User",
                email="admin@example.com",
                password_hash=hash_password("ChangeMe123!"),
                role=UserRole.admin,
            )
            db.add(admin)

        # Sample blocked sites
        samples = [
            ("porn", "regex", "C", "adult content"),
            ("facebook.com", "domain", "B", "social during hours"),
            ("http://bad.example.com/evil", "exact", "C", "malware"),
        ]
        for pattern, mtype, cat, reason in samples:
            db.add(
                BlockedSite(
                    url_pattern=pattern,
                    match_type=MatchType(mtype),
                    category=SiteCategory(cat),
                    reason=reason,
                )
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())

