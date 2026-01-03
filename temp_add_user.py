import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole

async def add_user():
    async with AsyncSessionLocal() as db:
        admin = User(
            id=uuid.uuid4(),
            name='Admin User',
            email='admin@example.com',
            password_hash=hash_password('ChangeMe123!'),
            role=UserRole.admin,
        )
        db.add(admin)
        await db.commit()
        print('User added')

asyncio.run(add_user())