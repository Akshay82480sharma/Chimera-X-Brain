import json
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import litellm

from app.db.models import Memory
from app.db.session import AsyncSessionLocal
from app.core.config import settings

from app.core.router import select_and_call_provider

async def extract_and_store_memory(user_content: str, conversation_id: int):
    """
    Background task to analyze user message, extract facts, 
    and save them to the Memory SQLite table.
    """
    if len(user_content) < 10:
        return # Too short to extract meaningful facts

    prompt = f"""
    Analyze the following message sent by the user to their AI assistant.
    Extract any persistent facts, preferences, or context about the user.
    Examples of facts: programming languages used, OS, projects they are working on, personal details, formatting preferences.
    If no persistent facts are found, return exactly this JSON: {{}}
    Otherwise, return a JSON object with key-value pairs representing the facts.
    Do NOT return any other text or markdown formatting. ONLY valid JSON.
    
    User Message: "{user_content}"
    """

    try:
        async with AsyncSessionLocal() as db:
            messages = [
                {"role": "system", "content": "You are a data extraction engine. You only output pure JSON."},
                {"role": "user", "content": prompt}
            ]
            
            # Use the auto-router instead of hardcoded litellm!
            # It will automatically detect task_type="extraction" and fall back to local models if cloud fails.
            provider_id, model_id, response = await select_and_call_provider(messages, db, stream=False)
            
            response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        # Clean markdown if accidentally generated
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
        try:
            facts = json.loads(response_text)
        except json.JSONDecodeError:
            return
        
        if facts and isinstance(facts, dict):
            async with AsyncSessionLocal() as db:
                for key, value in facts.items():
                    # Check if memory already exists
                    result = await db.execute(select(Memory).where(
                        (Memory.key == key) & (Memory.conversation_id == conversation_id)
                    ))
                    existing = result.scalars().first()
                    
                    if existing:
                        existing.content = str(value)
                    else:
                        new_mem = Memory(key=key, content=str(value), conversation_id=conversation_id)
                        db.add(new_mem)
                
                await db.commit()
                print(f"Memory Extracted: {facts}")

    except Exception as e:
        print(f"Memory extraction failed: {e}")
