import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Agent
from app.routing.prompt_builder import PromptBuilderService
from app.routing.router import select_and_call_provider

logger = logging.getLogger(__name__)

async def handle_delegate_to_agent(agent_name: str, task_description: str, chat_id: int, db: AsyncSession) -> str:
    """
    Spawns an internal task routed through the agent's specific persona.
    """
    logger.info(f"Delegating task to agent '{agent_name}' for chat {chat_id}")
    
    # Verify agent exists
    stmt = select(Agent).where(Agent.name == agent_name)
    result = await db.execute(stmt)
    agent = result.scalars().first()
    
    if not agent:
        return f"Error: Agent '{agent_name}' does not exist. Please use a valid agent name."

    # Build context specific to this agent
    prompt_builder = PromptBuilderService(db)
    # We pass the agent_name so it swaps the system prompt
    context = await prompt_builder.build_context(chat_id, max_tokens=8192, agent_name=agent_name)
    
    # Append the specific task
    context.append({"role": "user", "content": f"[DELEGATED TASK]\n{task_description}"})
    
    try:
        # Call the router
        # Note: We do not pass `chat_id` and `prompt_builder` kwargs here because we already built 
        # the context and we want to pass raw messages to skip the standard build_context inside router.
        # Wait, the router handles raw messages correctly now!
        provider_id, model_id, response = await select_and_call_provider(
            messages=context,
            db=db,
            stream=False
        )
        
        response_text = ""
        if isinstance(response, dict):
            response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        elif hasattr(response, "choices"):
            response_text = response.choices[0].message.content.strip()
            
        return f"Response from {agent_name}:\n\n{response_text}"
        
    except Exception as e:
        logger.error(f"Failed to delegate to agent: {e}")
        return f"Error: Failed to execute task with agent '{agent_name}': {str(e)}"
