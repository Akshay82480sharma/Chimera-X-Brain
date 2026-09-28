"""Tools API routes — CRUD for registered plugins."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Any

from app.db.session import get_db
from app.db.models import Tool

router = APIRouter(prefix="/v1/tools", tags=["Tools"])


class ToolCreate(BaseModel):
    name: str
    description: str
    input_schema: dict
    handler_type: str = "python_function"
    config: Optional[dict] = None
    is_active: bool = True


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    input_schema: Optional[dict] = None
    handler_type: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tool).order_by(Tool.name))
    return result.scalars().all()


@router.post("")
async def create_tool(data: ToolCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tool).where(Tool.name == data.name))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Tool with this name already exists")

    tool = Tool(
        name=data.name,
        description=data.description,
        input_schema=data.input_schema,
        handler_type=data.handler_type,
        config=data.config,
        is_active=data.is_active
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool


@router.post("/{tool_id}")
async def update_tool(
    tool_id: int,
    data: ToolUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalars().first()

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if data.name is not None:
        tool.name = data.name
    if data.description is not None:
        tool.description = data.description
    if data.input_schema is not None:
        tool.input_schema = data.input_schema
    if data.handler_type is not None:
        tool.handler_type = data.handler_type
    if data.config is not None:
        tool.config = data.config
    if data.is_active is not None:
        tool.is_active = data.is_active

    await db.commit()
    await db.refresh(tool)
    return tool


@router.delete("/{tool_id}")
async def delete_tool(tool_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
        
    await db.delete(tool)
    await db.commit()
    return {"status": "success"}
