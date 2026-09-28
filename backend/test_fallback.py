import asyncio
import httpx
import json

async def test_fallback():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        print("1. Creating Provider A (High Priority - Fake Key -> Will Fail)")
        r = await client.post("/v1/providers", json={
            "slug": "fake-openai",
            "name": "Fake OpenAI",
            "type": "cloud",
            "api_key": "sk-fake123",
            "is_active": True,
            "priority": 10
        })
        print(r.json())
        p_a = r.json()

        print("2. Creating Provider B (Lower Priority - Fake Key -> Will Fail too)")
        r = await client.post("/v1/providers", json={
            "slug": "fake-anthropic",
            "name": "Fake Anthropic",
            "type": "cloud",
            "api_key": "sk-fake456",
            "is_active": True,
            "priority": 20
        })
        print(r.json())
        p_b = r.json()
        
        # Add a model for both
        print("3. Syncing Models (Will fail for fake, let's create manually)")
        # we can't create models via API right now (only sync).
        pass
        
    print("Test script setup complete.")

asyncio.run(test_fallback())
