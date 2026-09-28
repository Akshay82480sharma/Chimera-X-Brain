import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Provider, AIModel
from sqlalchemy import select, update
import re

async def test_smart_router():
    async with AsyncSessionLocal() as db:
        providers = (await db.execute(select(Provider))).scalars().all()
        if len(providers) < 2:
            print("Need at least 2 providers for this test.")
            return
            
        p_cloud = next((p for p in providers if p.type != 'local'), providers[0])
        p_local = next((p for p in providers if p.type == 'local'), providers[1])
        
        p_cloud.priority = 10
        p_local.priority = 5
        db.add_all([p_cloud, p_local])
        await db.commit()
            
        print(f"\nSet P1 ({p_cloud.name}, Cloud) to Priority {p_cloud.priority}")
        print(f"Set P2 ({p_local.name}, Local) to Priority {p_local.priority}")
        
        m_cloud_small = AIModel(provider_id=p_cloud.id, model_name="llama-3-8b", is_active=True, task_tags="code")
        m_cloud_large = AIModel(provider_id=p_cloud.id, model_name="qwen-72b", is_active=True, task_tags="code")
        
        m_local_small = AIModel(provider_id=p_local.id, model_name="mistral-7b", is_active=True, task_tags="code")
        m_local_large = AIModel(provider_id=p_local.id, model_name="llama-70b", is_active=True, task_tags="code")
        
        db.add_all([m_cloud_small, m_cloud_large, m_local_small, m_local_large])
        await db.commit()
        
        print("\nSimulating the new router candidates block for task_type='code':")
        ordered_providers = [p_cloud, p_local]
        task_type = "code"
        
        candidates = [
            (p_cloud, m_cloud_small),
            (p_cloud, m_cloud_large),
            (p_local, m_local_small),
            (p_local, m_local_large),
        ]
                
        def sort_key(item):
            p, m = item
            size = 0.0
            match = re.search(r'(\d+(?:\.\d+)?)b\b', m.model_name.lower())
            if match:
                size = float(match.group(1))
                
            hardware_penalty = 0
            if size > 15.0 and p.type == 'local':
                hardware_penalty = 1000
            elif size <= 15.0 and size > 0 and p.type != 'local':
                hardware_penalty = 100
                
            is_match = bool(m.task_tags and task_type in m.task_tags)
            return (hardware_penalty, not is_match, p.priority)
            
        candidates.sort(key=sort_key)
        
        print("\nSorted Candidates (Lower score is better):")
        for idx, (p, m) in enumerate(candidates):
            size = 0.0
            match = re.search(r'(\d+(?:\.\d+)?)b\b', m.model_name.lower())
            if match: size = float(match.group(1))
            
            penalty = 0
            if size > 15.0 and p.type == 'local': penalty = 1000
            elif size <= 15.0 and size > 0 and p.type != 'local': penalty = 100
                
            print(f"{idx+1}. {m.model_name} (Provider: {p.type}, Penalty: {penalty}, Priority: {p.priority})")
            
        assert candidates[0][1].model_name == m_local_small.model_name, "Local small model should be #1"
        assert candidates[3][1].model_name == m_local_large.model_name, "Local large model should be LAST"

if __name__ == "__main__":
    asyncio.run(test_smart_router())
