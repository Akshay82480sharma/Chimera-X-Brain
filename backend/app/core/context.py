"""Context builder — the SACRED SEAM of Chimera-X.

This module builds the full message context for an AI completion call.
It is 100% model-agnostic and provider-agnostic.

╔══════════════════════════════════════════════════════════════════╗
║  GOLDEN RULE: This file must have ZERO knowledge of providers.  ║
║  No provider imports, no provider conditionals, no model names. ║
║  If you need to check "if provider == X", STOP and flag it.     ║
╚══════════════════════════════════════════════════════════════════╝

Context is built PURELY from:
  1. conversation_id → Message history
  2. conversation_id → Memory facts (injected as system context)
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message, Memory, PromptTemplate


SYSTEM_PROMPT = """You are Chimera-X, a helpful personal AI assistant. \
You have persistent memory and can remember facts about the user across conversations. \
Be concise, accurate, and helpful."""

MEMORY_INJECTION_TEMPLATE = """Here are known facts about the user (from persistent memory):
{memory_block}

Use these facts to personalize your responses when relevant, but don't \
explicitly mention that you're reading from a memory database."""


async def build_context(
    conversation_id: int,
    db: AsyncSession,
) -> list[dict]:
    """Build the full message context for a completion call.

    Returns a list of {"role": ..., "content": ...} dicts ready to pass
    directly to any LLM provider. This function has ZERO knowledge of
    which provider will consume the context.

    Args:
        conversation_id: The chat/conversation ID to load history from.
        db: An async database session.

    Returns:
        A list of message dicts: system prompt + memories + conversation history.
    """
    context: list[dict] = []

    # 1. System prompt
    default_prompt_result = await db.execute(
        select(PromptTemplate)
        .where(PromptTemplate.is_default == True)
    )
    default_prompt = default_prompt_result.scalars().first()
    
    system_content = default_prompt.content if default_prompt else SYSTEM_PROMPT
    context.append({"role": "system", "content": system_content})

    # 2. Inject relevant memories as additional system context
    memory_result = await db.execute(
        select(Memory)
        .where(
            (Memory.conversation_id == conversation_id)
            | (Memory.conversation_id.is_(None))  # Global memories
        )
        .order_by(Memory.created_at)
    )
    memories = memory_result.scalars().all()

    if memories:
        memory_lines = [f"- {m.key}: {m.content}" for m in memories]
        memory_block = "\n".join(memory_lines)
        context.append({
            "role": "system",
            "content": MEMORY_INJECTION_TEMPLATE.format(memory_block=memory_block),
        })

    # 3. Conversation history — ordered by creation time
    #    NOTE: We select role + content ONLY. We deliberately ignore
    #    provider_id and model_id — those are display metadata, not context.
    msg_result = await db.execute(
        select(Message)
        .where(Message.chat_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    # 3.5 RAG Injection (Knowledge Base)
    from app.api.knowledge import retrieve_relevant_chunks
    from app.db.models import Chat
    
    latest_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), None)
    
    if latest_user_msg:
        # Get project id for this chat
        result = await db.execute(select(Chat).where(Chat.id == conversation_id))
        chat = result.scalars().first()
        project_id = chat.project_id if chat and chat.project_id else 1
        
        relevant_chunks = await retrieve_relevant_chunks(latest_user_msg, project_id, 3, db)
        if relevant_chunks:
            rag_context = "Relevant information from the knowledge base:\n" + "\n\n".join(relevant_chunks)
            context.append({
                "role": "system",
                "content": rag_context,
            })

    import json
    for msg in messages:
        if msg.role == "assistant":
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict) and "tool_calls" in parsed:
                    msg_dict = {"role": "assistant"}
                    if parsed.get("text"):
                        msg_dict["content"] = parsed["text"]
                    if parsed.get("tool_calls"):
                        msg_dict["tool_calls"] = parsed["tool_calls"]
                    context.append(msg_dict)
                else:
                    context.append({"role": msg.role, "content": msg.content})
            except:
                context.append({"role": msg.role, "content": msg.content})
        elif msg.role == "tool":
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict) and "tool_call_id" in parsed:
                    context.append({
                        "role": "tool", 
                        "tool_call_id": parsed["tool_call_id"], 
                        "name": parsed.get("name", ""),
                        "content": parsed.get("content", "")
                    })
                else:
                    context.append({"role": msg.role, "content": msg.content})
            except:
                context.append({"role": msg.role, "content": msg.content})
        else:
            context.append({"role": msg.role, "content": msg.content})

    return context
