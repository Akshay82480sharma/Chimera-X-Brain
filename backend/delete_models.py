import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import AIModel
from sqlalchemy import select, delete

async def main():
    async with AsyncSessionLocal() as db:
        # Delete models that have openrouter in the name, or all of the ones in that list
        models_to_delete = [
            "minimaxai/minimax-m3", "nvidia/nemotron-3-ultra-550b-a55b", 
            "moonshotai/kimi-k2.6", "stepfun-ai/step-3.7-flash", 
            "mistralai/mistral-medium-3.5-128b", "deepseek-ai/deepseek-v4-pro", 
            "deepseek-ai/deepseek-v4-flash", "minimaxai/minimax-m2.7", 
            "google/gemma-4-31b-it", "qwen/qwen3.5-122b-a10b", 
            "nvidia/llama-3.3-nemotron-super-49b-v1.5", "qwen/qwen3.5-397b-a17b", 
            "openai/gpt-oss-120b", "google/diffusiongemma-26b-a4b-it"
        ]
        stmt = delete(AIModel).where(AIModel.model_name.in_(models_to_delete))
        result = await db.execute(stmt)
        await db.commit()
        print(f"Deleted models: {result.rowcount}")

if __name__ == "__main__":
    asyncio.run(main())
