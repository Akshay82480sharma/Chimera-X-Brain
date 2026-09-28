import asyncio
import sys
from pathlib import Path
import json

# Add the backend directory to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.db.session import AsyncSessionLocal
from app.db.models import Tool
from sqlalchemy import select

async def seed_tools():
    tools_to_seed = [
        {
            "name": "read_file",
            "description": "Reads the text content of a file on the local filesystem.",
            "handler_type": "python_function",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute or relative path to the file you want to read."
                    }
                },
                "required": ["path"]
            }
        },
        {
            "name": "write_file",
            "description": "Writes or overwrites content to a file on the local filesystem. Creates parent directories if needed.",
            "handler_type": "python_function",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute or relative path to the file you want to write to."
                    },
                    "content": {
                        "type": "string",
                        "description": "The full text content to write into the file."
                    }
                },
                "required": ["path", "content"]
            }
        },
        {
            "name": "list_directory",
            "description": "Lists all files and subdirectories inside a specific directory on the local filesystem.",
            "handler_type": "python_function",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute or relative path to the directory you want to list."
                    }
                },
                "required": ["path"]
            }
        },
        {
            "name": "run_command",
            "description": "Executes a shell command on the local machine (e.g. npm, python, git, mkdir). Returns stdout and stderr.",
            "handler_type": "python_function",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Optional. The working directory to run the command in. Defaults to the AI Workspace."
                    }
                },
                "required": ["command"]
            }
        }
    ]

    async with AsyncSessionLocal() as db:
        for t_data in tools_to_seed:
            result = await db.execute(select(Tool).where(Tool.name == t_data["name"]))
            existing = result.scalars().first()
            if not existing:
                new_tool = Tool(
                    name=t_data["name"],
                    description=t_data["description"],
                    handler_type=t_data["handler_type"],
                    input_schema=t_data["input_schema"],
                    is_active=True
                )
                db.add(new_tool)
                print(f"Added tool: {t_data['name']}")
            else:
                existing.description = t_data["description"]
                existing.input_schema = t_data["input_schema"]
                print(f"Updated tool: {t_data['name']}")
                
        await db.commit()
        print("Done seeding tools.")

if __name__ == "__main__":
    asyncio.run(seed_tools())
