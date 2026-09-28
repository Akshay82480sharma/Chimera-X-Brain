"""Memory API routes — CRUD for persistent memory facts."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Memory
from app.db.repositories.memory import MemoryRepository

router = APIRouter(prefix="/v1/memory", tags=["Memory"])


@router.get("")
async def list_memories(db: AsyncSession = Depends(get_db)):
    repo = MemoryRepository(db)
    return await repo.get_all_recent()


@router.post("")
async def add_memory(key: str, content: str, db: AsyncSession = Depends(get_db)):
    repo = MemoryRepository(db)
    memory = await repo.create({"key": key, "content": content})
    return memory


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, db: AsyncSession = Depends(get_db)):
    repo = MemoryRepository(db)
    success = await repo.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "success"}
