from app.models import User
from passlib.context import CryptContext
from app.core.database import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import settings
import asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def create_user():
    async with SessionLocal() as session:
        hashed_password = pwd_context.hash("string")  # login password

        user = User(
            name="Test User",              # REQUIRED: not null in DB
            email="user@example.com",
            password_hash=hashed_password,
            role="admin",                  # must match your ENUM
            is_active=True
        )

        session.add(user)
        await session.commit()
        print("🔥 User created successfully!")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await create_user()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
