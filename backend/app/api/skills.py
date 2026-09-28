from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import Skill
from app.db.repositories.skill import SkillRepository

router = APIRouter(prefix="/v1/skills", tags=["skills"])

class SkillCreate(BaseModel):
    name: str
    content: str

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None

class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    content: str

@router.get("", response_model=List[SkillResponse])
async def list_skills(db: AsyncSession = Depends(get_db)):
    try:
        repo = SkillRepository(db)
        stmt = select(repo.model_cls).order_by(repo.model_cls.created_at.desc())
        result = await db.execute(stmt)
        skills = result.scalars().all()
        return skills
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        raise HTTPException(status_code=500, detail=str(err))

@router.post("", response_model=SkillResponse)
async def create_skill(skill: SkillCreate, db: AsyncSession = Depends(get_db)):
    repo = SkillRepository(db)
    existing = await repo.get_by_name(skill.name)
    if existing:
        raise HTTPException(status_code=400, detail="Skill with this name already exists")
    
    db_skill = await repo.create({
        "name": skill.name,
        "content": skill.content,
    })
    return db_skill

@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(skill_id: int, updates: SkillUpdate, db: AsyncSession = Depends(get_db)):
    repo = SkillRepository(db)
    existing = await repo.get_by_id(skill_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Skill not found")
        
    update_data = updates.model_dump(exclude_unset=True)
    db_skill = await repo.update(existing, update_data)
    return db_skill

@router.delete("/{skill_id}")
async def delete_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    repo = SkillRepository(db)
    success = await repo.delete(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "success"}
