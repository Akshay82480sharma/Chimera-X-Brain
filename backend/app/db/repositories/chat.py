from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete

from app.db.repositories.base import BaseRepository
from app.db.models import Chat, Message

class ChatRepository(BaseRepository[Chat]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Chat)

    async def get_chat_with_messages(self, chat_id: int) -> Optional[Chat]:
        stmt = (
            select(Chat)
            .options(selectinload(Chat.messages))
            .filter(Chat.id == chat_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_recent_chats(self, limit: int = 50) -> List[Chat]:
        stmt = select(Chat).order_by(Chat.updated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_all(self):
        await self.session.execute(delete(Chat))
        await self.session.commit()


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)

    async def get_messages_by_chat(self, chat_id: int) -> List[Message]:
        stmt = select(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
