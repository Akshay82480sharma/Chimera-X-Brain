import asyncio
from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.db.models import Message

async def clean():
    async with AsyncSessionLocal() as db:
        result = await db.execute(delete(Message).where(Message.content == ''))
        await db.commit()
        print('Cleaned empty messages!')

asyncio.run(clean())
