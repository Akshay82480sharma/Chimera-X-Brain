import os
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import SkillNode
from app.learning.config import learning_settings
import logging

logger = logging.getLogger(__name__)

async def export_dataset(db: AsyncSession) -> dict:
    """
    Exports approved skills into a JSONL format suitable for training.
    """
    os.makedirs(learning_settings.dataset_dir, exist_ok=True)
    
    result = await db.execute(select(SkillNode).where(SkillNode.status == "approved"))
    skills = result.scalars().all()
    
    if not skills:
        return {"error": "No approved skills available for export."}
        
    train_path = os.path.join(learning_settings.dataset_dir, "train.jsonl")
    
    with open(train_path, "w", encoding="utf-8") as f:
        for skill in skills:
            # Simple conversational proxy for the SLM
            record = {"text": f"Fact: {skill.content}"}
            f.write(json.dumps(record) + "\n")
            
    meta_path = os.path.join(learning_settings.dataset_dir, "metadata.json")
    IST = timezone(timedelta(hours=5, minutes=30))
    meta = {
        "exported_at": datetime.now(IST).isoformat(),
        "samples": len(skills),
        "source": "chimera-x-brain"
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
        
    logger.info(f"Exported {len(skills)} samples to {learning_settings.dataset_dir}")
    return {"status": "success", "samples": len(skills), "path": train_path}
