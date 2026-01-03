import asyncio
from sqlalchemy import text
from app.core.database import engine

async def drop_table():
    async with engine.begin() as conn:
        await conn.execute(text('DROP TABLE IF EXISTS users CASCADE'))
        print('Dropped users table')

asyncio.run(drop_table())