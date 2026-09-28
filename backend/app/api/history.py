from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models import Chat, Message, Memory

router = APIRouter(prefix="/v1/chats", tags=["Chat History"])

class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    provider_id: Optional[int] = None
    model_id: Optional[int] = None
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[ChatResponse])
async def list_chats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat).order_by(desc(Chat.updated_at)))
    chats = result.scalars().all()
    return chats

@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def list_messages(chat_id: int, db: AsyncSession = Depends(get_db)):
    # Join Message with Provider and AIModel to get human readable names
    from app.db.models import Provider, AIModel
    
    query = (
        select(Message, Provider.name, AIModel.display_name)
        .outerjoin(Provider, Message.provider_id == Provider.id)
        .outerjoin(AIModel, Message.model_id == AIModel.id)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
    )
    
    result = await db.execute(query)
    
    # Construct the response dicts manually since we have joined columns
    response = []
    for msg, prov_name, mod_name in result:
        response.append({
            "id": msg.id,
            "chat_id": msg.chat_id,
            "role": msg.role,
            "content": msg.content,
            "provider_id": msg.provider_id,
            "model_id": msg.model_id,
            "provider_name": prov_name,
            "model_name": mod_name,
            "created_at": msg.created_at
        })
        
    return response

@router.delete("/{chat_id}")
async def delete_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if chat:
        await db.delete(chat)
        await db.commit()
    return {"status": "success"}

@router.delete("/all/clear")
async def clear_all_history(db: AsyncSession = Depends(get_db)):
    # Clear Messages, Chats, and Memories
    from sqlalchemy import delete
    await db.execute(delete(Message))
    await db.execute(delete(Chat))
    await db.execute(delete(Memory))
    await db.commit()
    return {"status": "success", "message": "All chat history and memories have been permanently deleted."}
