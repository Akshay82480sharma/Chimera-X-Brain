from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.repositories.base import BaseRepository
from app.db.models import Skill

class SkillRepository(BaseRepository[Skill]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Skill)

    async def get_by_name(self, name: str) -> Optional[Skill]:
        stmt = select(Skill).where(Skill.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()
