import re
import logging
from app.db.models import SkillNode
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def extract_and_queue_skills(prompt: str, response: str, chat_id: int):
    """
    Background task to silently extract facts from the LLM's response.
    Instead of auto-training, it marks them as 'pending' for the human review queue.
    """
    try:
        facts = []
        gaps = []
        
        # Simple heuristic extraction (can be replaced by advanced NLP later)
        sentences = [s.strip() for s in re.split(r'[.!?]', response) if s.strip()]
        for s in sentences:
            if " is " in s or " are " in s:
                facts.append(s)
            elif " I don't know" in s or " I am not sure" in s:
                gaps.append(s)
                
        confidence = 100 if not gaps else 40
        
        if not facts:
            return
            
        async with AsyncSessionLocal() as db:
            for fact in facts:
                skill = SkillNode(
                    chat_id=chat_id,
                    content=fact,
                    confidence=confidence,
                    provenance="model",
                    status="pending" # Placed in review queue
                )
                db.add(skill)
                
            await db.commit()
            logger.info(f"Extracted {len(facts)} skills into review queue from chat_id {chat_id}")
        
    except Exception as e:
        logger.error(f"Failed to extract and queue skills: {e}")
