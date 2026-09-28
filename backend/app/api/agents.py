from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import Agent
from app.db.repositories.agent import AgentRepository

router = APIRouter(prefix="/v1/agents", tags=["agents"])

class AgentCreate(BaseModel):
    name: str
    system_prompt: str
    tools_allowed: Optional[List[int]] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    tools_allowed: Optional[List[int]] = None

from pydantic import BaseModel, ConfigDict

class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    system_prompt: str
    tools_allowed: Optional[List[int]] = None

@router.get("", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    try:
        repo = AgentRepository(db)
        stmt = select(repo.model_cls).order_by(repo.model_cls.created_at.desc())
        result = await db.execute(stmt)
        agents = result.scalars().all()
        return agents
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        raise HTTPException(status_code=500, detail=str(err))

@router.post("", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: AsyncSession = Depends(get_db)):
    repo = AgentRepository(db)
    existing = await repo.get_by_name(agent.name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")
    
    db_agent = await repo.create({
        "name": agent.name,
        "system_prompt": agent.system_prompt,
        "tools_allowed": agent.tools_allowed or []
    })
    return db_agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, updates: AgentUpdate, db: AsyncSession = Depends(get_db)):
    repo = AgentRepository(db)
    existing = await repo.get_by_id(agent_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    update_data = updates.model_dump(exclude_unset=True)
    db_agent = await repo.update(existing, update_data)
    return db_agent

@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    repo = AgentRepository(db)
    success = await repo.delete(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "success"}
