"""Prompts API routes — CRUD for Prompt Templates."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.db.session import get_db
from app.db.models import PromptTemplate

router = APIRouter(prefix="/v1/prompts", tags=["Prompts"])


class PromptTemplateCreate(BaseModel):
    name: str
    content: str
    tags: Optional[list[str]] = None
    is_default: bool = False


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    is_default: Optional[bool] = None


@router.get("")
async def list_prompts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromptTemplate).order_by(PromptTemplate.name))
    return result.scalars().all()


@router.post("")
async def create_prompt(data: PromptTemplateCreate, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.name == data.name))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Prompt with this name already exists")
        
    if data.is_default:
        # Unset previous default
        old_default = await db.execute(select(PromptTemplate).where(PromptTemplate.is_default == True))
        for old in old_default.scalars().all():
            old.is_default = False

    prompt = PromptTemplate(
        name=data.name,
        content=data.content,
        tags=data.tags,
        is_default=data.is_default
    )
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.post("/{prompt_id}")
async def update_prompt(
    prompt_id: int,
    data: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == prompt_id))
    prompt = result.scalars().first()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if data.is_default:
        old_default = await db.execute(select(PromptTemplate).where(PromptTemplate.is_default == True))
        for old in old_default.scalars().all():
            old.is_default = False

    if data.name is not None:
        prompt.name = data.name
    if data.content is not None:
        prompt.content = data.content
    if data.tags is not None:
        prompt.tags = data.tags
    if data.is_default is not None:
        prompt.is_default = data.is_default

    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == prompt_id))
    prompt = result.scalars().first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
        
    await db.delete(prompt)
    await db.commit()
    return {"status": "success"}
