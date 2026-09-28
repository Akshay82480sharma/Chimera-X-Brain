import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import get_db
from sqlalchemy.future import select
from app.db.models import Agent, Skill
from app.retrieval.vector_store import vector_store

async def backfill():
    print("Starting backfill...")
    async for db in get_db():
        # Backfill Agents
        print("Backfilling agents...")
        result = await db.execute(select(Agent))
        agents = result.scalars().all()
        for agent in agents:
            vector_store.add_agent(agent.id, agent.system_prompt, {"name": agent.name})
            print(f"Added agent: {agent.name}")

        # Backfill Skills
        print("Backfilling skills...")
        result = await db.execute(select(Skill))
        skills = result.scalars().all()
        for skill in skills:
            vector_store.add_skill(skill.id, skill.content, {"name": skill.name})
            print(f"Added skill: {skill.name}")

        break # only need one session
    print("Backfill complete.")

if __name__ == "__main__":
    asyncio.run(backfill())
