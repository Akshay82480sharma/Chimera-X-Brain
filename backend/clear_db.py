import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Chat, Message, Memory
from sqlalchemy import delete

async def clear():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Message))
        await db.execute(delete(Chat))
        await db.execute(delete(Memory))
        await db.commit()
        print('History cleared.')

if __name__ == "__main__":
    asyncio.run(clear())
