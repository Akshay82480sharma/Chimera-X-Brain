from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.ecc_sync import sync_ecc_repository, get_ecc_status

router = APIRouter(prefix="/v1/ecc", tags=["ECC"])

@router.post("/sync")
async def sync_ecc(db: AsyncSession = Depends(get_db)):
    """Trigger a synchronization with the upstream ECC GitHub repository."""
    return await sync_ecc_repository(db)

@router.get("/status")
async def ecc_status(db: AsyncSession = Depends(get_db)):
    """Get the current count of imported ECC skills and agents."""
    return await get_ecc_status(db)
