from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls

    async def get_by_id(self, id: int) -> Optional[T]:
        result = await self.session.execute(select(self.model_cls).filter(self.model_cls.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        result = await self.session.execute(select(self.model_cls).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, obj_in: Dict[str, Any]) -> T:
        db_obj = self.model_cls(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: T, obj_in: Dict[str, Any]) -> T:
        for field in obj_in:
            setattr(db_obj, field, obj_in[field])
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        db_obj = await self.get_by_id(id)
        if db_obj:
            await self.session.execute(delete(self.model_cls).where(self.model_cls.id == id))
            await self.session.commit()
            return True
        return False
