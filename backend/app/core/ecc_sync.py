import os
import io
import zipfile
import httpx
import asyncio
import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import PromptTemplate, Agent, Skill

logger = logging.getLogger(__name__)

GITHUB_ZIP_URL = "https://github.com/affaan-m/ECC/archive/refs/heads/main.zip"

async def sync_ecc_repository(db: AsyncSession) -> dict:
    """Download the ECC repo and import agents, skills, and rules into their respective tables."""
    logger.info("Starting ECC repository sync...")
    
    try:
        # 1. Download the ZIP file
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(GITHUB_ZIP_URL)
            response.raise_for_status()
            zip_content = response.content

        # 2. Extract and parse in-memory
        imported_count = 0
        with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
            for file_info in z.infolist():
                if file_info.is_dir() or not file_info.filename.endswith(".md"):
                    continue
                
                parts = file_info.filename.split('/')
                if len(parts) < 3:
                    continue
                    
                category = parts[1] # e.g., 'agents', 'skills', 'rules'
                if category not in ["agents", "skills", "rules"]:
                    continue
                    
                filename = parts[-1]
                name = filename.replace(".md", "")
                content = z.read(file_info).decode("utf-8")
                
                if category == "agents":
                    stmt = select(Agent).where(Agent.name == f"[ECC] {name}")
                    existing = (await db.execute(stmt)).scalar_one_or_none()
                    if existing:
                        existing.system_prompt = content
                        agent_obj = existing
                    else:
                        agent_obj = Agent(name=f"[ECC] {name}", system_prompt=content, tools_allowed=[])
                        db.add(agent_obj)
                    
                    await db.flush()
                    from app.retrieval.vector_store import vector_store
                    import asyncio
                    await asyncio.to_thread(vector_store.add_agent, agent_obj.id, content, {"name": agent_obj.name})
                        
                elif category == "skills":
                    stmt = select(Skill).where(Skill.name == f"[ECC] {name}")
                    existing = (await db.execute(stmt)).scalar_one_or_none()
                    if existing:
                        existing.content = content
                        skill_obj = existing
                    else:
                        skill_obj = Skill(name=f"[ECC] {name}", content=content)
                        db.add(skill_obj)
                    
                    await db.flush()
                    from app.retrieval.vector_store import vector_store
                    import asyncio
                    await asyncio.to_thread(vector_store.add_skill, skill_obj.id, content, {"name": skill_obj.name})
                        
                elif category == "rules":
                    tag = "ecc-rule"
                    stmt = select(PromptTemplate).where(PromptTemplate.name == f"[ECC] {name}")
                    existing = (await db.execute(stmt)).scalar_one_or_none()
                    if existing:
                        existing.content = content
                        existing.tags = tag
                    else:
                        db.add(PromptTemplate(name=f"[ECC] {name}", content=content, tags=tag, is_default=False))
                
                imported_count += 1
                
        await db.commit()
        logger.info(f"ECC sync complete. Imported {imported_count} files.")
        return {"status": "success", "imported": imported_count}
        
    except Exception as e:
        logger.error(f"Failed to sync ECC repository: {e}")
        return {"status": "error", "detail": str(e)}

async def get_ecc_status(db: AsyncSession) -> dict:
    """Return the count of ECC entities currently in the database."""
    
    agent_count = (await db.execute(select(Agent).where(Agent.name.like("[ECC] %")))).scalars().all()
    skill_count = (await db.execute(select(Skill).where(Skill.name.like("[ECC] %")))).scalars().all()
    rule_count = (await db.execute(select(PromptTemplate).where(PromptTemplate.name.like("[ECC] %")))).scalars().all()
    
    counts = {
        "agents": len(agent_count),
        "skills": len(skill_count),
        "rules": len(rule_count),
        "total": len(agent_count) + len(skill_count) + len(rule_count)
    }
    return counts
