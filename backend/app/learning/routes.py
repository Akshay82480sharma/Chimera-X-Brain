from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import subprocess
import os

from app.db.session import get_db
from app.db.models import SkillNode
from app.learning import review, dataset

router = APIRouter()

class SkillUpdate(BaseModel):
    content: str

@router.get("/skills/pending")
async def get_pending_skills(db: AsyncSession = Depends(get_db)):
    """Fetch skills waiting in the review queue."""
    result = await db.execute(select(SkillNode).where(SkillNode.status == "pending"))
    return result.scalars().all()

@router.put("/skills/{skill_id}/approve")
async def approve_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    success = await review.approve_skill(skill_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "approved"}

@router.put("/skills/{skill_id}/reject")
async def reject_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    success = await review.reject_skill(skill_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "rejected"}

@router.put("/skills/{skill_id}")
async def edit_skill(skill_id: int, req: SkillUpdate, db: AsyncSession = Depends(get_db)):
    success = await review.edit_skill(skill_id, req.content, db)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "updated_and_approved"}

@router.post("/export")
async def export_training_data(db: AsyncSession = Depends(get_db)):
    """Exports approved skills into a training dataset."""
    return await dataset.export_dataset(db)

@router.post("/train")
async def trigger_training():
    """Triggers fine-tuning as an isolated background subprocess without blocking FastAPI."""
    trainer_script = os.path.join(os.path.dirname(__file__), "trainer.py")
    
    # We use Popen so the OS handles it, completely detaching it from FastAPI
    # In Windows, we can use creationflags to run in background, but standard Popen is sufficient to not block.
    subprocess.Popen(["python", trainer_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return {"status": "Training started in background."}
