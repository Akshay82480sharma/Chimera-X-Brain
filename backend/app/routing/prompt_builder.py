from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PromptTemplate
from app.db.repositories.chat import ChatRepository, MessageRepository
from app.db.repositories.memory import MemoryRepository
from sqlalchemy import select

SYSTEM_PROMPT = """You are Chimera-X, a helpful personal AI assistant. \
You have persistent memory and can remember facts about the user across conversations. \
Be concise, accurate, and helpful."""

MEMORY_INJECTION_TEMPLATE = """Here are known facts about the user (from persistent memory):
{memory_block}

Use these facts to personalize your responses when relevant, but don't \
explicitly mention that you're reading from a memory database."""


class PromptBuilderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.message_repo = MessageRepository(session)
        self.memory_repo = MemoryRepository(session)
        self.chat_repo = ChatRepository(session)

    async def build_context(
        self, 
        conversation_id: int, 
        max_tokens: int = 8192, 
        agent_name: str = None,
        agent_id: int = None,
        skill_ids: list[int] = None,
        auto_agent: bool = False,
        auto_skills: bool = False
    ) -> list[dict]:
        from app.utils.token_counter import get_token_count, get_messages_token_count
        from app.retrieval.retrieval_service import RetrievalService
        
        # 1. Budgeting
        response_reserve = 2048
        available_context = max_tokens - response_reserve
        if available_context < 1000:
            available_context = 1000 # hard minimum safety floor

        context: list[dict] = []
        
        # Get latest user message early for RAG
        messages = await self.message_repo.get_messages_by_chat(conversation_id)
        latest_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), None)

        # 2. System prompt
        system_content = SYSTEM_PROMPT
        if agent_id:
            from app.db.models import Agent
            agent_result = await self.session.execute(select(Agent).where(Agent.id == agent_id))
            agent = agent_result.scalars().first()
            if agent:
                system_content = agent.system_prompt
        elif auto_agent and latest_user_msg:
            # Vector RAG for Agent
            rag_agent = await RetrievalService.get_relevant_agent(latest_user_msg)
            if rag_agent:
                system_content = rag_agent["document"]
        elif agent_name:
            from app.db.models import Agent
            agent_result = await self.session.execute(select(Agent).where(Agent.name == agent_name))
            agent = agent_result.scalars().first()
            if agent:
                system_content = agent.system_prompt
        else:
            default_prompt_result = await self.session.execute(
                select(PromptTemplate).where(PromptTemplate.is_default == True)
            )
            default_prompt = default_prompt_result.scalars().first()
            system_content = default_prompt.content if default_prompt else SYSTEM_PROMPT
            
        # 2.5 Inject Manual/Auto Skills
        if skill_ids:
            from app.db.models import Skill
            skills_result = await self.session.execute(select(Skill).where(Skill.id.in_(skill_ids)))
            skills = skills_result.scalars().all()
            if skills:
                system_content += "\n\n--- IMPOSED SKILL INSTRUCTIONS ---\n"
                for skill in skills:
                    system_content += f"\n# SKILL: {skill.name}\n{skill.content}\n"
        elif auto_skills and latest_user_msg:
            rag_skills = await RetrievalService.get_relevant_skills(latest_user_msg)
            if rag_skills:
                system_content += "\n\n--- RELEVANT SKILLS ---\n"
                for skill in rag_skills:
                    name = skill["metadata"].get("name", "Unknown Skill") if skill.get("metadata") else "Unknown Skill"
                    system_content += f"\n# SKILL: {name}\n{skill['document']}\n"
        
        system_msg = {"role": "system", "content": system_content}
        system_tokens = get_messages_token_count([system_msg])
        available_context -= system_tokens
        context.append(system_msg)

        # 3. Conversation history (get all, then we'll truncate later)
        messages = await self.message_repo.get_messages_by_chat(conversation_id)
        
        latest_user_msg = None
        for m in reversed(messages):
            if m.role == "user":
                try:
                    parsed = json.loads(m.content)
                    if isinstance(parsed, list):
                        latest_user_msg = next((p.get("text", "") for p in parsed if p.get("type") == "text"), "")
                    else:
                        latest_user_msg = m.content
                except:
                    latest_user_msg = m.content
                break

        # 4. Inject relevant memories via Hybrid Search (budget max 20% of remaining context)
        from app.retrieval.retrieval_service import RetrievalService
        memory_budget = int(available_context * 0.20)
        memory_lines = []
        
        if latest_user_msg:
            semantic_memories = await RetrievalService.get_relevant_memories(latest_user_msg)
            for m in semantic_memories:
                line = f"- {m['document']}"
                if get_token_count("\n".join(memory_lines + [line])) < memory_budget:
                    memory_lines.append(line)
        
        # Also always include VERY recent memories as a baseline, if they fit
        recent_chat_memories = await self.memory_repo.get_memories_by_chat(conversation_id)
        for m in recent_chat_memories[:5]:
            mem_str = f"- {m.key}: {m.content}"
            if mem_str not in memory_lines:
                if get_token_count("\n".join(memory_lines + [mem_str])) < memory_budget:
                    memory_lines.append(mem_str)
        
        
        if latest_user_msg:
            # Inject Life Graph context
            graph_nodes = await RetrievalService.get_relevant_graph_context(latest_user_msg)
            for g in graph_nodes:
                line = f"- [LIFE GRAPH] {g['document']}"
                if get_token_count("\n".join(memory_lines + [line])) < memory_budget:
                    memory_lines.append(line)

        if memory_lines:
            memory_block = "\n".join(memory_lines)
            memory_msg = {
                "role": "system",
                "content": MEMORY_INJECTION_TEMPLATE.format(memory_block=memory_block),
            }
            mem_tokens = get_messages_token_count([memory_msg])
            available_context -= mem_tokens
            context.append(memory_msg)

        # 4.5 RAG Injection (budget max 30% of remaining context)
        from app.api.knowledge import retrieve_relevant_chunks
        rag_budget = int(available_context * 0.30)
        
        if latest_user_msg:
            chat = await self.chat_repo.get_by_id(conversation_id)
            project_id = chat.project_id if chat and chat.project_id else 1
            
            relevant_chunks = await retrieve_relevant_chunks(latest_user_msg, project_id, 3, self.session)
            if relevant_chunks:
                rag_content = "Relevant information from the knowledge base:\n"
                for chunk in relevant_chunks:
                    if get_token_count(rag_content + "\n\n" + chunk) < rag_budget:
                        rag_content += "\n\n" + chunk
                
                rag_msg = {"role": "system", "content": rag_content}
                rag_tokens = get_messages_token_count([rag_msg])
                available_context -= rag_tokens
                context.append(rag_msg)

        # 5. Assemble History within remaining budget
        import json
        history_msgs = []
        for msg in reversed(messages):
            if msg.role == "assistant":
                try:
                    parsed = json.loads(msg.content)
                    if isinstance(parsed, dict) and "tool_calls" in parsed:
                        msg_dict = {"role": "assistant"}
                        if parsed.get("text"):
                            msg_dict["content"] = parsed["text"]
                        if parsed.get("tool_calls"):
                            msg_dict["tool_calls"] = parsed["tool_calls"]
                        history_msgs.insert(0, msg_dict)
                    else:
                        history_msgs.insert(0, {"role": msg.role, "content": msg.content})
                except:
                    history_msgs.insert(0, {"role": msg.role, "content": msg.content})
            elif msg.role == "tool":
                try:
                    parsed = json.loads(msg.content)
                    if isinstance(parsed, dict) and "tool_call_id" in parsed:
                        history_msgs.insert(0, {
                            "role": "tool", 
                            "tool_call_id": parsed["tool_call_id"], 
                            "name": parsed.get("name", ""),
                            "content": parsed.get("content", "")
                        })
                    else:
                        history_msgs.insert(0, {"role": msg.role, "content": msg.content})
                except:
                    history_msgs.insert(0, {"role": msg.role, "content": msg.content})
            else:
                history_msgs.insert(0, {"role": msg.role, "content": msg.content})

        # Truncate history to fit budget
        final_history = []
        current_history_tokens = 0
        for msg in reversed(history_msgs):
            msg_tokens = get_messages_token_count([msg])
            if current_history_tokens + msg_tokens > available_context:
                break
            final_history.insert(0, msg)
            current_history_tokens += msg_tokens

        context.extend(final_history)
        return context
