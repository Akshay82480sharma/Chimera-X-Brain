from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.repositories.base import BaseRepository
from app.db.models import Agent

class AgentRepository(BaseRepository[Agent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Agent)

    async def get_by_name(self, name: str) -> Optional[Agent]:
        stmt = select(Agent).where(Agent.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()
