import asyncio
import json
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import AsyncSessionLocal
from app.db.models import Message
from app.db.repositories.graph import EntityRepository, RelationRepository
from app.routing.router import select_and_call_provider

logger = logging.getLogger(__name__)

REFLECTION_PROMPT = """You are the 'Evolution Engine' for a Personal AI Brain.
Your task is to analyze the following conversation and extract Knowledge Graph nodes (Entities) and edges (Relations) that represent the user's long-term goals, skills, ongoing projects, relationships, or major concepts.

Focus on "Life Intelligence":
- Goals (e.g., Become AI Engineer, Run Marathon)
- Skills/Learning (e.g., Python, System Design)
- Projects (e.g., Chimera-X, Portfolio Website)
- Relationships (e.g., John (friend), Jane (mentor))

Rules:
1. Extract ONLY persistent, long-term information. Ignore short-term trivialities.
2. Output your response as PURE JSON. Do not include markdown formatting or extra text.
3. Use the following JSON schema:
{
    "entities": [
        {"name": "String", "type": "Goal|Skill|Project|Person|Concept", "attributes": {"key": "value"}}
    ],
    "relations": [
        {"source_name": "String", "target_name": "String", "relation_type": "REQUIRES|IS_LEARNING|WORKING_ON|KNOWS|RELATED_TO", "weight": 100}
    ]
}

Conversation:
{chat_history}
"""

async def run_reflection_cycle(chat_id: int):
    """Analyzes a chat and extracts graph nodes/edges."""
    try:
        async with AsyncSessionLocal() as db:
            # 1. Fetch recent messages for context
            stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.id.desc()).limit(10)
            result = await db.execute(stmt)
            messages = list(result.scalars().all())
            messages.reverse()
            
            if not messages:
                return

            chat_history = "\n".join([f"{m.role}: {m.content}" for m in messages])
            prompt = REFLECTION_PROMPT.replace("{chat_history}", chat_history)

            # 2. Call LLM for extraction
            llm_messages = [{"role": "system", "content": prompt}]
            try:
                # Use standard router with default task classification (likely will pick a smart model for extraction)
                provider_id, model_id, response = await select_and_call_provider(messages=llm_messages, db=db, stream=False)
            except Exception as e:
                logger.warning(f"Evolution Engine skipped: {e}")
                return

            # 3. Parse JSON response
            response_text = ""
            if isinstance(response, dict):
                response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            elif hasattr(response, "choices"):
                response_text = response.choices[0].message.content.strip()

            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning(f"Evolution Engine failed to parse JSON: {response_text}")
                return

            # 4. Insert into Graph Database
            entity_repo = EntityRepository(db)
            relation_repo = RelationRepository(db)
            
            entity_id_map = {}

            # Create entities
            for ent in data.get("entities", []):
                name = ent.get("name")
                type_ = ent.get("type", "Concept")
                attrs = ent.get("attributes", {})
                
                if name:
                    # 'User' is implicitly always present, but let's keep it robust
                    db_ent = await entity_repo.create_entity(name, type_, attrs)
                    entity_id_map[name.lower()] = db_ent.id
            
            # Create relations
            for rel in data.get("relations", []):
                s_name = rel.get("source_name", "").lower()
                t_name = rel.get("target_name", "").lower()
                rel_type = rel.get("relation_type", "RELATED_TO")
                weight = rel.get("weight", 100)
                
                s_id = entity_id_map.get(s_name)
                t_id = entity_id_map.get(t_name)
                
                if s_id and t_id:
                    await relation_repo.create_relation(s_id, t_id, rel_type, weight)
                    
            logger.info(f"Evolution Engine extracted {len(entity_id_map)} entities from chat {chat_id}")

    except Exception as e:
        logger.error(f"Evolution Engine encountered an error: {e}")
