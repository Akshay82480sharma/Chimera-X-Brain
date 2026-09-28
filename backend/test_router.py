import asyncio
from datetime import datetime, timezone, timedelta
from app.db.session import AsyncSessionLocal, init_db
from app.db.models import Provider, AIModel
from app.core.router import select_and_call_provider

async def test_fallback():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Create Provider A
        p1 = Provider(slug="provider-a", name="Provider A", priority=10, is_active=True, api_key="fake")
        db.add(p1)
        # Create Provider B
        p2 = Provider(slug="provider-b", name="Provider B", priority=20, is_active=True, api_key="fake")
        db.add(p2)
        await db.commit()
        await db.refresh(p1)
        await db.refresh(p2)
        
        # Add Models
        m1 = AIModel(provider_id=p1.id, model_name="gpt-mock-1", is_active=True)
        db.add(m1)
        m2 = AIModel(provider_id=p2.id, model_name="gpt-mock-2", is_active=True)
        db.add(m2)
        await db.commit()
        
        # Test routing - Should try A, fail, try B, fail, raise Exception
        messages = [{"role": "user", "content": "Hello"}]
        try:
            await select_and_call_provider(messages, db, stream=False)
        except Exception as e:
            print(f"Final Exception: {e}")
            
        # Check if Provider A was rate limited
        await db.refresh(p1)
        await db.refresh(p2)
        print(f"Provider A rate limited? {p1.is_rate_limited}")
        print(f"Provider B rate limited? {p2.is_rate_limited}")

if __name__ == "__main__":
    asyncio.run(test_fallback())
