import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from app.db.session import AsyncSessionLocal, init_db
from app.db.models import Tool
from sqlalchemy.future import select

async def add_tool():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        stmt = select(Tool).where(Tool.name == "delegate_to_agent")
        result = await db.execute(stmt)
        tool = result.scalars().first()
        
        if not tool:
            new_tool = Tool(
                name="delegate_to_agent",
                description="Delegate a sub-task to a specialized internal agent. Use this when a task requires specialized expertise or a dedicated context.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "The exact name of the agent to delegate to (e.g. 'Backend Architect')."
                        },
                        "task_description": {
                            "type": "string",
                            "description": "A highly detailed description of the task the agent needs to perform."
                        }
                    },
                    "required": ["agent_name", "task_description"]
                },
                handler_type="delegate_to_agent",
                is_active=True
            )
            db.add(new_tool)
            await db.commit()
            print("Successfully added 'delegate_to_agent' tool to DB.")
        else:
            print("Tool 'delegate_to_agent' already exists.")

if __name__ == "__main__":
    asyncio.run(add_tool())
