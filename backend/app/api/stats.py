"""Stats API — provides data for the dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.session import get_db
from app.db.models import Provider, AIModel, Memory, Chat, RouterLog

router = APIRouter(prefix="/v1/stats", tags=["Stats"])


@router.get("")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate statistics for the system dashboard."""
    
    # 1. Total connected providers
    prov_result = await db.execute(select(func.count(Provider.id)))
    total_providers = prov_result.scalar_one()

    # 2. Total active models
    model_result = await db.execute(select(func.count(AIModel.id)).where(AIModel.is_active == True))
    active_models = model_result.scalar_one()
    
    # 3. Total chats (proxy for requests right now)
    chat_result = await db.execute(select(func.count(Chat.id)))
    total_chats = chat_result.scalar_one()

    # 4. Recent Memory Stream
    # We'll pull the 3 most recent memories to populate the dashboard stream
    # A memory could be from a Chat, or Global (we'll just use the memory key/content)
    # We join with Chat to get the chat title if available
    memory_query = (
        select(Memory, Chat.title)
        .outerjoin(Chat, Memory.conversation_id == Chat.id)
        .order_by(desc(Memory.created_at))
        .limit(3)
    )
    mem_result = await db.execute(memory_query)
    
    recent_memories = []
    for mem, chat_title in mem_result:
        # We simulate the provider "Memory System" or based on where it came from
        recent_memories.append({
            "id": mem.id,
            "title": f"Learned: {mem.key.capitalize()}",
            "type": "Fact" if mem.conversation_id is None else f"From: {chat_title or 'Unknown Chat'}",
            "date": mem.created_at.isoformat(),
            "provider": "Memory System",
            "content": mem.content
        })

    return {
        "metrics": {
            "total_providers": total_providers,
            "active_models": active_models,
            "total_chats": total_chats
        },
        "recent_memories": recent_memories
    }

@router.get("/router-tune")
async def router_tune(db: AsyncSession = Depends(get_db)):
    """Analyze RouterLogs and suggest new priorities for providers."""
    # Group logs by provider_to_id and calculate success rate and average latency
    logs_result = await db.execute(select(RouterLog))
    logs = logs_result.scalars().all()
    
    if not logs:
        return {"suggestions": []}
        
    stats = {}
    for log in logs:
        pid = log.provider_to_id
        if pid not in stats:
            stats[pid] = {"successes": 0, "failures": 0, "total_latency": 0, "latency_count": 0}
            
        if log.success:
            stats[pid]["successes"] += 1
            if log.latency_ms is not None:
                stats[pid]["total_latency"] += log.latency_ms
                stats[pid]["latency_count"] += 1
        else:
            stats[pid]["failures"] += 1
            
    # Calculate score (simple heuristic: success rate is king, then latency)
    scores = []
    for pid, s in stats.items():
        total = s["successes"] + s["failures"]
        if total == 0:
            continue
        success_rate = s["successes"] / total
        avg_latency = s["total_latency"] / s["latency_count"] if s["latency_count"] > 0 else 5000
        
        # Lower score is better (we want to use it as priority)
        # E.g. base 1000 - (success_rate * 500) + (avg_latency / 100)
        # 100% success, 500ms latency -> 1000 - 500 + 5 = 505
        score = int(1000 - (success_rate * 500) + (avg_latency / 100))
        scores.append({"provider_id": pid, "suggested_priority": score, "success_rate": success_rate, "avg_latency_ms": int(avg_latency)})
        
    # Sort by suggested priority
    scores.sort(key=lambda x: x["suggested_priority"])
    
    # Map back to provider names for the UI
    providers_result = await db.execute(select(Provider))
    providers = {p.id: p.name for p in providers_result.scalars().all()}
    
    suggestions = []
    for s in scores:
        provider_name = providers.get(s["provider_id"])
        if not provider_name:
            continue
            
        suggestions.append({
            "provider_name": provider_name,
            "provider_id": s["provider_id"],
            "suggested_priority": s["suggested_priority"],
            "success_rate": f"{s['success_rate']*100:.1f}%",
            "avg_latency_ms": s["avg_latency_ms"]
        })
        
    return {"suggestions": suggestions}
