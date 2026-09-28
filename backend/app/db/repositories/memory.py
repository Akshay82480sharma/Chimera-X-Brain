from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import asyncio

from app.db.repositories.base import BaseRepository
from app.db.models import Memory
from app.retrieval.vector_store import vector_store

class MemoryRepository(BaseRepository[Memory]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Memory)

    async def create(self, obj_in: Dict[str, Any]) -> Memory:
        db_obj = await super().create(obj_in)
        # Sync to Vector DB in a background thread to prevent blocking the event loop
        await asyncio.to_thread(
            vector_store.add_memory,
            memory_id=db_obj.id,
            text=f"{db_obj.key}: {db_obj.content}",
            metadata={"key": db_obj.key, "conversation_id": db_obj.conversation_id}
        )
        return db_obj

    async def delete(self, id: int) -> bool:
        success = await super().delete(id)
        if success:
            await asyncio.to_thread(vector_store.delete_memory, memory_id=id)
        return success

    async def get_memories_by_chat(self, chat_id: int) -> List[Memory]:
        stmt = select(Memory).filter(Memory.conversation_id == chat_id).order_by(Memory.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_recent(self, limit: int = 100) -> List[Memory]:
        stmt = select(Memory).order_by(Memory.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_all(self):
        await self.session.execute(delete(Memory))
        await self.session.commit()

