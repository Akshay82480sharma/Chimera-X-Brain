"""Providers API routes — CRUD for AI provider configurations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from app.db.session import get_db
from app.db.models import Provider, AIModel

router = APIRouter(prefix="/v1/providers", tags=["Providers"])


class ProviderCreate(BaseModel):
    slug: str
    name: str
    type: str = "cloud"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True
    priority: int = 100
    daily_quota_limit: Optional[int] = None


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    daily_quota_limit: Optional[int] = None


async def seed_standard_models(db: AsyncSession, provider: Provider):
    if provider.type == "local":
        return
        
    standard_models = {
        "openai": ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1"],
        "anthropic": ["claude-3-7-sonnet-20250219", "claude-3-5-haiku-20241022"],
        "zhipu": ["glm-4-plus", "glm-4-flash"],
        "moonshot": ["moonshot-v1-8k", "moonshot-v1-32k"],
        "minimax": ["abab6.5s-chat", "abab6.5g-chat"],
        "deepseek": ["deepseek-chat", "deepseek-reasoner"],
        "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-flash"],
    }
    
    slug_lower = provider.slug.lower()
    models_to_add = standard_models.get(slug_lower, [])
    
    if models_to_add:
        result = await db.execute(select(AIModel).where(AIModel.provider_id == provider.id))
        existing_names = {m.model_name for m in result.scalars().all()}
        
        for m_name in models_to_add:
            if m_name not in existing_names:
                new_model = AIModel(
                    provider_id=provider.id,
                    model_name=m_name,
                    display_name=m_name,
                    is_active=True
                )
                db.add(new_model)
        await db.commit()


@router.get("")
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Provider).order_by(Provider.priority))
    providers = result.scalars().all()
    
    # Lazily clear expired rate limits so the UI updates
    now = datetime.now(timezone.utc)
    for p in providers:
        if p.is_rate_limited and p.rate_limit_reset_at:
            reset_at = p.rate_limit_reset_at
            if reset_at.tzinfo is None:
                reset_at = reset_at.replace(tzinfo=timezone.utc)
            if now > reset_at:
                p.is_rate_limited = False
                p.rate_limit_reset_at = None
    
    await db.commit()
    return providers


@router.post("")
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db)):
    # Check slug uniqueness
    result = await db.execute(select(Provider).where(Provider.slug == data.slug))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail=f"Provider with slug '{data.slug}' already exists")

    provider = Provider(
        slug=data.slug,
        name=data.name,
        type=data.type,
        base_url=data.base_url,
        api_key=data.api_key,
        is_active=data.is_active,
        priority=data.priority,
        daily_quota_limit=data.daily_quota_limit,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    await seed_standard_models(db, provider)
    return provider


@router.post("/{provider_slug}")
async def update_provider(
    provider_slug: str,
    data: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Provider).where(Provider.slug == provider_slug))
    provider = result.scalars().first()

    if not provider:
        # Auto-create if it doesn't exist (backward compat with frontend)
        provider = Provider(
            slug=provider_slug,
            name=data.name or provider_slug,
            type=data.type or "cloud",
            base_url=data.base_url,
            api_key=data.api_key,
            is_active=data.is_active if data.is_active is not None else True,
            priority=data.priority or 100,
            daily_quota_limit=data.daily_quota_limit,
        )
        db.add(provider)
    else:
        if data.name is not None:
            provider.name = data.name
        if data.type is not None:
            provider.type = data.type
        if data.base_url is not None:
            provider.base_url = data.base_url
        if data.api_key is not None:
            provider.api_key = data.api_key
        if data.is_active is not None:
            provider.is_active = data.is_active
        if data.priority is not None:
            provider.priority = data.priority
        if data.daily_quota_limit is not None:
            provider.daily_quota_limit = data.daily_quota_limit

    await db.commit()
    await db.refresh(provider)
    await seed_standard_models(db, provider)
    return provider


@router.delete("/{provider_slug}")
async def delete_provider(provider_slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Provider).where(Provider.slug == provider_slug))
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await db.delete(provider)
    await db.commit()
    return {"status": "success"}
