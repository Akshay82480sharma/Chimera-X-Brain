"""Models API routes — list and sync AI models from providers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import httpx

from app.db.session import get_db, AsyncSessionLocal
from app.db.models import Provider, AIModel

router = APIRouter(prefix="/v1/models", tags=["Models"])


class ModelResponse(BaseModel):
    id: int
    provider_id: int
    model_name: str
    display_name: Optional[str] = None
    task_tags: Optional[list] = None
    size_gb: Optional[float] = 0.0
    is_active: bool = True
    provider_slug: str
    provider_name: str
    provider_type: str

    class Config:
        from_attributes = True


class ModelUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    task_tags: Optional[list] = None
    size_gb: Optional[float] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_models(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            AIModel.id,
            AIModel.provider_id,
            AIModel.model_name,
            AIModel.display_name,
            AIModel.task_tags,
            AIModel.size_gb,
            AIModel.is_active,
            Provider.slug.label("provider_slug"),
            Provider.name.label("provider_name"),
            Provider.type.label("provider_type")
        )
        .join(Provider, AIModel.provider_id == Provider.id)
    )
    result = await db.execute(query)
    
    models = []
    for row in result.all():
        models.append({
            "id": row.id,
            "provider_id": row.provider_id,
            "model_name": row.model_name,
            "display_name": row.display_name,
            "task_tags": row.task_tags,
            "size_gb": row.size_gb,
            "is_active": row.is_active,
            "provider_slug": row.provider_slug,
            "provider_name": row.provider_name,
            "provider_type": row.provider_type
        })
    return models

class ModelCreate(BaseModel):
    provider_id: int
    model_name: str
    display_name: str

@router.post("")
async def create_model(data: ModelCreate, db: AsyncSession = Depends(get_db)):
    # verify provider exists
    result = await db.execute(select(Provider).where(Provider.id == data.provider_id))
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    model = AIModel(
        provider_id=data.provider_id,
        model_name=data.model_name,
        display_name=data.display_name
    )
    db.add(model)
    await db.commit()
    return {"status": "success"}


@router.post("/sync")
async def sync_models():
    """Pings active local providers and syncs available models. Auto-discovers local engines."""
    
    # 1. Fetch data quickly
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Provider).where(Provider.slug.in_(["lm-studio", "ollama"])))
        existing_providers = {p.slug: {"id": p.id, "name": p.name} for p in result.scalars().all()}
        
        result = await db.execute(select(Provider).where(Provider.is_active == True))
        active_providers = []
        for p in result.scalars().all():
            if not p.base_url: continue
            if p.type == "local" or "localhost" in p.base_url or "127.0.0.1" in p.base_url:
                active_providers.append({"id": p.id, "slug": p.slug, "base_url": p.base_url})
                
    auto_targets = [
        {"slug": "lm-studio", "name": "LM Studio", "url": "http://127.0.0.1:1234/v1"},
        {"slug": "ollama", "name": "Ollama", "url": "http://127.0.0.1:11434/v1"},
    ]
    
    # 2. Network calls without DB locks
    auto_errors = []
    new_providers = []
    async with httpx.AsyncClient(timeout=2.0) as client:
        for target in auto_targets:
            if target["slug"] not in existing_providers:
                try:
                    res = await client.get(f"{target['url']}/models")
                    if res.status_code == 200:
                        new_providers.append(target)
                except Exception as e:
                    if target["slug"] == "lm-studio":
                        auto_errors.append(f"Auto-discover LM Studio failed: {str(e)}")

    if new_providers:
        async with AsyncSessionLocal() as db:
            for p in new_providers:
                new_prov = Provider(
                    slug=p["slug"], name=p["name"], type="local",
                    base_url=p["url"], is_active=True
                )
                db.add(new_prov)
            await db.commit()
            
            # Now fetch them back to get their assigned IDs
            for p in new_providers:
                result = await db.execute(select(Provider).where(Provider.slug == p["slug"]))
                prov_db = result.scalars().first()
                if prov_db:
                    active_providers.append({"id": prov_db.id, "slug": prov_db.slug, "base_url": prov_db.base_url})

    synced_models = []
    errors = list(auto_errors)
    models_to_add = []
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for p in active_providers:
            try:
                url = p["base_url"].rstrip("/")
                if not url.endswith("/models"):
                    url = f"{url}/models" if url.endswith("/v1") else f"{url}/v1/models"

                response = await client.get(url)
                if response.status_code == 200:
                    models_data = response.json().get("data", [])
                    for m in models_data:
                        m_id = m.get("id")
                        if m_id:
                            models_to_add.append({"provider_id": p["id"], "model_name": m_id})
                else:
                    errors.append(f"{p['slug']}: HTTP {response.status_code}")
            except Exception as e:
                errors.append(f"{p['slug']}: {str(e)}")

    # 3. Apply model updates
    async with AsyncSessionLocal() as db:
        for m in models_to_add:
            model_result = await db.execute(
                select(AIModel).where(
                    AIModel.model_name == m["model_name"],
                    AIModel.provider_id == m["provider_id"]
                )
            )
            if not model_result.scalars().first():
                display = m["model_name"].split("/")[-1] if "/" in m["model_name"] else m["model_name"]
                new_model = AIModel(
                    provider_id=m["provider_id"],
                    model_name=m["model_name"],
                    display_name=display
                )
                db.add(new_model)
                synced_models.append(m["model_name"])
        await db.commit()
        
    return {"status": "success", "synced": len(synced_models), "models": synced_models, "errors": errors}


@router.put("/{model_id}")
async def update_model(model_id: int, request: ModelUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
        
    if request.display_name is not None:
        model.display_name = request.display_name
    if request.task_tags is not None:
        model.task_tags = request.task_tags
    if request.size_gb is not None:
        model.size_gb = request.size_gb
    if request.is_active is not None:
        model.is_active = request.is_active
        
    await db.commit()
    return {"status": "success"}


@router.delete("/{model_id}")
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await db.delete(model)
    await db.commit()
    return {"status": "success"}
