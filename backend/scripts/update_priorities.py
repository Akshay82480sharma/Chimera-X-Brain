import asyncio
import sys
from pathlib import Path

# Add the backend directory to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.db.session import AsyncSessionLocal
from app.db.models import Provider
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Provider))
        providers = result.scalars().all()
        for p in providers:
            print(f'{p.id}: {p.name} - {p.type} - priority={p.priority}')
        
        print('\nUpdating priorities...')
        for p in providers:
            if p.type == 'cloud':
                p.priority = 1
            else:
                p.priority = 5
        await db.commit()
        print('Done!')
        
if __name__ == "__main__":
    asyncio.run(main())
