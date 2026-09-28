from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import asyncio

from app.db.repositories.base import BaseRepository
from app.db.models import Entity, Relation
from app.retrieval.vector_store import vector_store

class EntityRepository(BaseRepository[Entity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Entity)

    async def create_entity(self, name: str, type: str, attributes: dict = None) -> Entity:
        # Check if exists
        stmt = select(Entity).where(Entity.name == name, Entity.type == type)
        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            # Update attributes if provided
            if attributes:
                if not existing.attributes:
                    existing.attributes = {}
                existing.attributes.update(attributes)
                await self.session.commit()
            return existing

        # Create new
        db_obj = Entity(name=name, type=type, attributes=attributes or {})
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)

        # Sync to Vector DB
        await asyncio.to_thread(
            vector_store.add_entity,
            entity_id=db_obj.id,
            text=f"[{type}] {name}: {attributes or ''}",
            metadata={"name": name, "type": type}
        )
        return db_obj

class RelationRepository(BaseRepository[Relation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Relation)

    async def create_relation(self, source_id: int, target_id: int, relation_type: str, weight: int = 100) -> Relation:
        # Check if exists
        stmt = select(Relation).where(
            Relation.source_id == source_id,
            Relation.target_id == target_id,
            Relation.relation_type == relation_type
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            return existing

        db_obj = Relation(source_id=source_id, target_id=target_id, relation_type=relation_type, weight=weight)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
