import asyncio
import logging
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models import Provider

logger = logging.getLogger(__name__)

# Track consecutive failures per provider ID
_failure_counts: dict[int, int] = {}

async def check_provider_health():
    """Ping each active provider and update health status."""
    provider_data = []
    
    # 1. Fetch active providers quickly
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Provider).where(Provider.is_active == True))
        for p in result.scalars().all():
            provider_data.append({
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "base_url": p.base_url,
                "is_rate_limited": p.is_rate_limited
            })
            
    if not provider_data:
        return
        
    # 2. Perform network checks outside DB transaction
    updates = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for p in provider_data:
            if p["type"] == "cloud":
                _failure_counts[p["id"]] = 0
                continue
                
            try:
                url = (p["base_url"] or "").rstrip("/")
                if not url:
                    continue
                if not url.endswith("/models"):
                    if url.endswith("/v1"):
                        url = f"{url}/models"
                    else:
                        url = f"{url}/v1/models"
                response = await client.get(url)
                if response.status_code == 200:
                    _failure_counts[p["id"]] = 0
                    if p["is_rate_limited"]:
                        updates.append({"id": p["id"], "rate_limited": False, "reset_at": None})
                        logger.info(f"Provider {p['name']} recovered.")
                else:
                    _failure_counts[p["id"]] = _failure_counts.get(p["id"], 0) + 1
                    logger.warning(f"Health check failed for {p['name']}: HTTP {response.status_code}")
            except Exception as e:
                _failure_counts[p["id"]] = _failure_counts.get(p["id"], 0) + 1
                logger.warning(f"Health check failed for {p['name']}: {e}")
            
            # If 3 consecutive failures, mark as rate limited with 5-min cooldown
            if _failure_counts.get(p["id"], 0) >= 3 and not p["is_rate_limited"]:
                updates.append({
                    "id": p["id"], 
                    "rate_limited": True, 
                    "reset_at": datetime.now(timezone.utc) + timedelta(minutes=5),
                    "error_at": datetime.now(timezone.utc)
                })
                logger.error(f"Provider {p['name']} marked unhealthy after 3 failures.")
                
    # 3. Apply updates if any
    if updates:
        async with AsyncSessionLocal() as db:
            for upd in updates:
                res = await db.execute(select(Provider).where(Provider.id == upd["id"]))
                prov = res.scalars().first()
                if prov:
                    prov.is_rate_limited = upd["rate_limited"]
                    prov.rate_limit_reset_at = upd.get("reset_at")
                    if "error_at" in upd:
                        prov.last_error_at = upd["error_at"]
            await db.commit()


async def health_check_loop():
    """Run health checks every 60 seconds."""
    while True:
        try:
            await check_provider_health()
        except Exception as e:
            logger.error(f"Health check loop error: {e}")
        await asyncio.sleep(60)
