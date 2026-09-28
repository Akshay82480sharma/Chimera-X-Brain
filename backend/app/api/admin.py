"""Admin API routes — dashboard activity data and database management."""

import os
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta

from app.db.session import get_db, engine
from app.db.models import RouterLog, Provider, Chat, Message, Memory, PromptTemplate, Tool

router = APIRouter(prefix="/v1/admin", tags=["Admin"])


@router.get("/activity")
async def get_routing_activity(db: AsyncSession = Depends(get_db)):
    """Return routing log entries for the activity chart.
    Groups by hour for the last 24 hours.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(RouterLog)
        .where(RouterLog.timestamp >= cutoff)
        .order_by(RouterLog.timestamp)
    )
    logs = result.scalars().all()
    
    # Group by hour
    hourly: dict[str, dict] = {}
    for log in logs:
        hour_key = log.timestamp.strftime("%Y-%m-%d %H:00")
        if hour_key not in hourly:
            hourly[hour_key] = {"hour": hour_key, "success": 0, "failure": 0, "total": 0, "avg_latency": 0, "latencies": []}
        hourly[hour_key]["total"] += 1
        if log.success:
            hourly[hour_key]["success"] += 1
        else:
            hourly[hour_key]["failure"] += 1
        if log.latency_ms:
            hourly[hour_key]["latencies"].append(log.latency_ms)
    
    # Calculate averages
    activity = []
    for h in hourly.values():
        h["avg_latency"] = int(sum(h["latencies"]) / len(h["latencies"])) if h["latencies"] else 0
        del h["latencies"]
        activity.append(h)
    
    return {"activity": activity}


@router.delete("/wipe")
async def wipe_database(db: AsyncSession = Depends(get_db)):
    """Erase all user data (chats, messages, memories, prompts, tools, logs).
    Providers are kept intact since they contain API keys.
    """
    await db.execute(Message.__table__.delete())
    await db.execute(Chat.__table__.delete())
    await db.execute(Memory.__table__.delete())
    await db.execute(PromptTemplate.__table__.delete())
    await db.execute(Tool.__table__.delete())
    await db.execute(RouterLog.__table__.delete())
    await db.commit()
    return {"status": "success", "message": "All user data wiped. Providers preserved."}
