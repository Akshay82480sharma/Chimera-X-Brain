import json
import logging
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Memory
from app.db.repositories.memory import MemoryRepository
from app.routing.router import select_and_call_provider

logger = logging.getLogger(__name__)

async def extract_and_store_memory(user_content: str, conversation_id: int):
    """
    Background task to analyze user message, extract facts, 
    and save them to the Memory database and ChromaDB.
    """
    if len(user_content) < 10:
        return # Too short to extract meaningful facts

    prompt = f"""
    Analyze the following message sent by the user to their AI assistant.
    Extract any persistent facts, preferences, or context about the user.
    Examples of facts: programming languages used, OS, projects they are working on, personal details, formatting preferences.
    
    Format your response as a pure JSON object of key-value pairs. 
    The 'key' should be a short, 1-3 word identifier (e.g., "favorite_language", "current_os").
    The 'value' should be a descriptive, semantic sentence (e.g., "The user's favorite programming language is Python.").
    
    If no persistent facts are found, return exactly this JSON: {{}}
    Do NOT return any other text or markdown formatting. ONLY valid JSON.
    
    User Message: "{user_content}"
    """

    try:
        async with AsyncSessionLocal() as db:
            messages = [
                {"role": "system", "content": "You are a data extraction engine. You only output pure JSON."},
                {"role": "user", "content": prompt}
            ]
            
            # The auto-router will detect task_type="extraction" and route appropriately
            try:
                provider_id, model_id, response = await select_and_call_provider(messages, db, stream=False)
            except Exception as e:
                logger.warning(f"Memory extraction skipped: Router failed to find a provider: {e}")
                return
                
            response_text = ""
            # Handle different litellm response object types safely
            if isinstance(response, dict):
                response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            elif hasattr(response, "choices"):
                response_text = response.choices[0].message.content.strip()
        
        # Clean markdown if accidentally generated
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
            
        try:
            facts = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse memory JSON: {response_text}")
            return
        
        if facts and isinstance(facts, dict) and len(facts) > 0:
            async with AsyncSessionLocal() as db:
                memory_repo = MemoryRepository(db)
                for key, value in facts.items():
                    # Check if memory key already exists for this chat
                    result = await db.execute(select(Memory).where(
                        (Memory.key == key) & (Memory.conversation_id == conversation_id)
                    ))
                    existing = result.scalars().first()
                    
                    if existing:
                        # Update via repository (which triggers ChromaDB update)
                        # The MemoryRepository currently only syncs on create/delete. 
                        # We'll delete and recreate to ensure ChromaDB gets updated properly.
                        await memory_repo.delete(existing.id)
                        
                    await memory_repo.create({
                        "key": key,
                        "content": str(value),
                        "conversation_id": conversation_id
                    })
                
                logger.info(f"Memory Extracted & Embedded: {facts}")

    except Exception as e:
        logger.error(f"Memory extraction completely failed: {e}")
