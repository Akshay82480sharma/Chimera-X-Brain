import asyncio
import sys
from pathlib import Path

# Add the backend directory to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.db.session import AsyncSessionLocal
from app.db.models import RouterLog, Provider
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RouterLog).order_by(RouterLog.timestamp.desc()).limit(5))
        logs = result.scalars().all()
        for log in logs:
            result_p = await db.execute(select(Provider).where(Provider.id == log.provider_to_id))
            p = result_p.scalars().first()
            if p:
                print(f'Provider: {p.name} | Success: {log.success} | Error: {log.reason}')
            else:
                print(f'Provider ID: {log.provider_to_id} | Success: {log.success} | Error: {log.reason}')
        
if __name__ == "__main__":
    asyncio.run(main())
