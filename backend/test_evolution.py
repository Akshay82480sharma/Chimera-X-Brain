import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from app.db.session import AsyncSessionLocal, init_db
from app.db.models import Chat, Message
from app.learning.evolution_engine import run_reflection_cycle
from app.db.repositories.graph import EntityRepository, RelationRepository
from sqlalchemy.future import select

async def run_test():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Create dummy chat
        chat = Chat(title="Test Life Graph")
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        # Add some messages that should trigger entity extraction
        msgs = [
            Message(chat_id=chat.id, role="user", content="I am starting to learn Java because I want to become a Senior Backend Engineer."),
            Message(chat_id=chat.id, role="assistant", content="That's a great goal! Java is heavily used in enterprise backend systems."),
            Message(chat_id=chat.id, role="user", content="Yeah, my friend Jane recommended I learn Spring Boot next.")
        ]
        db.add_all(msgs)
        await db.commit()
        
        print(f"Created Test Chat {chat.id}")
        print("Running Evolution Engine (Reflection Cycle)...")
        
    await run_reflection_cycle(chat.id)
    
    async with AsyncSessionLocal() as db:
        ent_repo = EntityRepository(db)
        rel_repo = RelationRepository(db)
        
        ents = await db.execute(select(ent_repo.model))
        entities = ents.scalars().all()
        print("\n--- EXTRACTED ENTITIES ---")
        for e in entities:
            print(f"[{e.type}] {e.name} (Attrs: {e.attributes})")
            
        rels = await db.execute(select(rel_repo.model))
        relations = rels.scalars().all()
        print("\n--- EXTRACTED RELATIONS ---")
        for r in relations:
            s = await db.execute(select(ent_repo.model).where(ent_repo.model.id == r.source_id))
            t = await db.execute(select(ent_repo.model).where(ent_repo.model.id == r.target_id))
            source = s.scalars().first()
            target = t.scalars().first()
            if source and target:
                print(f"{source.name} --({r.relation_type})--> {target.name}")

if __name__ == "__main__":
    asyncio.run(run_test())
