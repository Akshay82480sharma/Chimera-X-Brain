from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import SkillNode

async def approve_skill(skill_id: int, db: AsyncSession) -> bool:
    result = await db.execute(select(SkillNode).where(SkillNode.id == skill_id))
    skill = result.scalars().first()
    if skill:
        skill.status = "approved"
        skill.provenance = "human" # Marking as human-verified
        await db.commit()
        return True
    return False

async def reject_skill(skill_id: int, db: AsyncSession) -> bool:
    result = await db.execute(select(SkillNode).where(SkillNode.id == skill_id))
    skill = result.scalars().first()
    if skill:
        skill.status = "rejected"
        await db.commit()
        return True
    return False

async def edit_skill(skill_id: int, new_content: str, db: AsyncSession) -> bool:
    result = await db.execute(select(SkillNode).where(SkillNode.id == skill_id))
    skill = result.scalars().first()
    if skill:
        skill.content = new_content
        skill.status = "approved"
        skill.provenance = "human"
        await db.commit()
        return True
    return False
