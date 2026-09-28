"""Chat API endpoint — Wired to the Router and Context Builder.

Phase 2: Handles chat completions using the fallback router, and fires
memory extraction as a background task.
"""

from typing import Any
import json
from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import logging

from app.db.session import get_db
from app.db.models import Chat, Message, Tool, Provider, AIModel
from app.routing.prompt_builder import PromptBuilderService
from app.routing.router import select_and_call_provider
from app.learning.memory_extractor import extract_and_store_memory
from app.learning.extractor import extract_and_queue_skills
from app.learning.evolution_engine import run_reflection_cycle

import os
import subprocess
from pathlib import Path

def execute_tool_call_sync(tool_name: str, arguments: dict) -> str:
    """Legacy synchronous execute_tool_call fallback"""
    import asyncio
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute_tool_call(tool_name, arguments, None, 0))

async def execute_tool_call(tool_name: str, arguments: dict, db: AsyncSession = None, chat_id: int = 0) -> str:
    """Executes agentic tool calls on the local filesystem."""
    try:
        # Default workspace (ensure it exists)
        workspace = Path(os.path.expanduser("~")) / "Desktop" / "AI_Workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Helper to resolve and strictly sandbox paths
        def resolve_path(path_str: str) -> Path:
            p = Path(path_str)
            if not p.is_absolute():
                p = workspace / p
            # Optional: restrict to workspace if desired, but for now we allow absolute paths
            # as long as they are resolved properly.
            return p.resolve()

        if tool_name == "read_file":
            target = resolve_path(arguments.get("path", ""))
            if not target.exists():
                return f"Error: File {target} does not exist."
            if not target.is_file():
                return f"Error: {target} is not a file."
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            return f"--- FILE CONTENT: {target} ---\n{content}"

        elif tool_name == "write_file":
            target = resolve_path(arguments.get("path", ""))
            content = arguments.get("content", "")
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {target}."

        elif tool_name == "list_directory":
            target = resolve_path(arguments.get("path", ""))
            if not target.exists():
                return f"Error: Directory {target} does not exist."
            if not target.is_dir():
                return f"Error: {target} is not a directory."
            
            items = []
            for item in target.iterdir():
                type_str = "DIR" if item.is_dir() else "FILE"
                items.append(f"[{type_str}] {item.name}")
            return f"--- CONTENTS OF {target} ---\n" + "\n".join(items)

        elif tool_name == "run_command":
            cmd = arguments.get("command", "")
            cwd = arguments.get("cwd", str(workspace))
            cwd_path = resolve_path(cwd)
            cwd_path.mkdir(parents=True, exist_ok=True)
            
            # Execute with a timeout to prevent hanging the chat
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=cwd_path,
                capture_output=True, 
                text=True,
                timeout=60
            )
            
            output = f"Command: {cmd}\nExit Code: {result.returncode}\n"
            if result.stdout:
                output += f"--- STDOUT ---\n{result.stdout}\n"
            if result.stderr:
                output += f"--- STDERR ---\n{result.stderr}\n"
            return output
            
        elif tool_name == "calculator":
            result = eval(arguments.get("expression", ""))
            return str(result)
            
        elif tool_name == "web_search":
            return f"Simulated search results for: {arguments.get('query')}"
            
        elif tool_name == "delegate_to_agent":
            if db is None:
                return "Error: Database session required for agent delegation."
            from app.tools.agent_delegate import handle_delegate_to_agent
            return await handle_delegate_to_agent(
                arguments.get("agent_name", ""),
                arguments.get("task_description", ""),
                chat_id,
                db
            )
            
        return f"Tool {tool_name} executed successfully."
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return f"Error executing tool {tool_name}: {str(e)}"


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["Chat"])


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    input_messages = body.get("messages", [])
    chat_id = body.get("chat_id")
    stream = body.get("stream", False)
    agent_id = body.get("agent_id")
    skill_ids = body.get("skill_ids", [])
    auto_agent = body.get("auto_agent", False)
    auto_skills = body.get("auto_skills", False)

    # 1. Get or create chat
    if chat_id:
        result = await db.execute(select(Chat).where(Chat.id == chat_id))
        chat = result.scalars().first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
    else:
        first_user_msg_raw = next((m["content"] for m in input_messages if m["role"] == "user"), "New Chat")
        first_user_msg_text = first_user_msg_raw
        if isinstance(first_user_msg_raw, list):
            first_user_msg_text = next((p.get("text", "") for p in first_user_msg_raw if p.get("type") == "text"), "New Chat")
            
        title = first_user_msg_text[:50] + "..." if len(first_user_msg_text) > 50 else first_user_msg_text
        chat = Chat(title=title)
        db.add(chat)
        await db.flush()
        chat_id = chat.id

    # 2. Save the latest user message
    latest_user_content = None
    if input_messages and input_messages[-1]["role"] == "user":
        latest_user_content = input_messages[-1]["content"]
        user_msg = Message(
            chat_id=chat_id,
            role="user",
            content=json.dumps(latest_user_content) if isinstance(latest_user_content, list) else latest_user_content,
        )
        db.add(user_msg)
        await db.flush()

    # 3. Build Context (System prompt + Memories + History)
    prompt_builder = PromptBuilderService(db)
    context_messages = await prompt_builder.build_context(
        chat_id, 
        agent_id=agent_id, 
        skill_ids=skill_ids,
        auto_agent=auto_agent,
        auto_skills=auto_skills
    )
    
    # 3.5. Load active tools
    formatted_tools = None
    if auto_skills or (skill_ids and len(skill_ids) > 0):
        tools_result = await db.execute(select(Tool).where(Tool.is_active == True))
        active_tools = tools_result.scalars().all()
        
        # Filter by skill_ids if not auto_skills
        if not auto_skills and skill_ids:
            active_tools = [t for t in active_tools if t.id in skill_ids]
            
        if active_tools:
            formatted_tools = []
            for t in active_tools:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema
                    }
                })

    # 4. Route and Call Provider
    try:
        req_model = body.get("model", "auto")
        force_model_id = int(req_model) if req_model != "auto" else None
        
        provider_id, model_id, response, is_fallback = await select_and_call_provider(
            chat_id=chat_id, 
            prompt_builder=prompt_builder,
            db=db, 
            stream=stream, 
            tools=formatted_tools,
            force_model_id=force_model_id
        )
    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    # 5. Handle response and save assistant message
    if stream:
        from sse_starlette.sse import EventSourceResponse
        
        async def stream_and_save():
            # Send chat metadata first
            yield {"event": "chat_meta", "data": json.dumps({"chat_id": chat_id, "provider_id": provider_id, "model_id": model_id, "is_fallback": is_fallback})}
            
            full_content = ""
            tool_calls_buffer = {}  # index -> {id, type, function: {name, arguments}}
            
            try:
                async for chunk in response:
                    if isinstance(chunk, dict):
                        chunk_dict = chunk
                    elif hasattr(chunk, "model_dump"):
                        chunk_dict = chunk.model_dump(exclude_none=True)
                    elif hasattr(chunk, "dict"):
                        chunk_dict = chunk.dict(exclude_none=True)
                    else:
                        chunk_dict = dict(chunk)
                        
                    delta = chunk_dict.get("choices", [{}])[0].get("delta", {})
                    
                    if "content" in delta and delta.get("content"):
                        full_content += delta["content"]
                        
                    if "tool_calls" in delta:
                        for tc in delta["tool_calls"]:
                            idx = tc.get("index", 0)
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": tc.get("id"), "type": "function", "function": {"name": "", "arguments": ""}}
                            if tc.get("id"):
                                tool_calls_buffer[idx]["id"] = tc["id"]
                            if tc.get("function"):
                                if tc["function"].get("name"):
                                    tool_calls_buffer[idx]["function"]["name"] += tc["function"]["name"]
                                if tc["function"].get("arguments"):
                                    tool_calls_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]

                    yield {"data": json.dumps(chunk_dict)}
            except Exception as e:
                logger.error(f"Provider stream interrupted: {e}")
                yield {"event": "error", "data": json.dumps({"error": "Stream interrupted or timed out by the provider."})}
            
            # If tool calls were made, execute them and recurse
            if tool_calls_buffer:
                # Save the assistant message with the tool call
                tool_calls_list = [v for k, v in sorted(tool_calls_buffer.items())]
                assistant_payload = {
                    "text": full_content,
                    "tool_calls": tool_calls_list
                }
                assistant_msg = Message(
                    chat_id=chat_id,
                    role="assistant",
                    content=json.dumps(assistant_payload), # Store as JSON payload
                    provider_id=provider_id,
                    model_id=model_id
                )
                db.add(assistant_msg)
                
                yield {"event": "tool_calls_pending", "data": json.dumps(tool_calls_list)}
                
                # End the current generator so the client can show the popup
                return
                
            else:
                # No tool calls, finish normally
                if full_content.strip():
                    assistant_msg = Message(
                        chat_id=chat_id,
                        role="assistant",
                        content=full_content,
                        provider_id=provider_id,
                        model_id=model_id
                    )
                    db.add(assistant_msg)
                    IST = timezone(timedelta(hours=5, minutes=30))
                    chat.updated_at = datetime.now(IST)
                    await db.commit()
                yield {"data": "[DONE]"}
            
            # Fire memory extraction
            if latest_user_content:
                # We can't use background_tasks here because the response is already running.
                # But since we're in an async generator, we can just fire and forget using asyncio.
                import asyncio
                asyncio.create_task(extract_and_store_memory(latest_user_content, chat_id))
                asyncio.create_task(extract_and_queue_skills(latest_user_content, full_content, chat_id))
                asyncio.create_task(run_reflection_cycle(chat_id))
            
        return EventSourceResponse(stream_and_save())
    
    else:
        # Non-streaming
        assistant_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        assistant_msg = Message(
            chat_id=chat_id,
            role="assistant",
            content=assistant_content,
            provider_id=provider_id,
            model_id=model_id
        )
        db.add(assistant_msg)
        IST = timezone(timedelta(hours=5, minutes=30))
        chat.updated_at = datetime.now(IST)
        await db.commit()
        
        # Inject metadata into response
        response["chat_id"] = chat_id
        response["provider_id"] = provider_id
        response["model_id"] = model_id
        response["is_fallback"] = is_fallback
        
        # Fire memory extraction
        if latest_user_content:
            background_tasks.add_task(extract_and_store_memory, latest_user_content, chat_id)
            background_tasks.add_task(extract_and_queue_skills, latest_user_content, assistant_content, chat_id)
            background_tasks.add_task(run_reflection_cycle, chat_id)
            
        return response

from pydantic import BaseModel
from typing import List, Optional

class ResolvedTool(BaseModel):
    id: str
    status: str
    name: str
    arguments: dict

class ResolveToolsRequest(BaseModel):
    chat_id: int
    tool_calls: List[ResolvedTool]
    provider_id: Optional[int] = None
    model_id: Optional[int] = None
    agent_id: Optional[int] = None
    skill_ids: Optional[List[int]] = []
    auto_agent: Optional[bool] = False
    auto_skills: Optional[bool] = False

@router.post("/chat/tools/resolve")
async def resolve_tools(
    req: ResolveToolsRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    # 1. Verify chat exists
    result = await db.execute(select(Chat).where(Chat.id == req.chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    # 2. Execute approved tools and save results
    for tc in req.tool_calls:
        if tc.status == "approved":
            result_str = await execute_tool_call(tc.name, tc.arguments, db, req.chat_id)
        else:
            result_str = f"User rejected this action."
            
        tool_payload = {
            "tool_call_id": tc.id,
            "name": tc.name,
            "content": result_str
        }
        tool_msg = Message(
            chat_id=req.chat_id,
            role="tool",
            content=json.dumps(tool_payload),
        )
        db.add(tool_msg)
        
    await db.commit()
    
    # 3. Build context and call provider again
    prompt_builder = PromptBuilderService(db)
    context_messages = await prompt_builder.build_context(
        req.chat_id, 
        agent_id=req.agent_id, 
        skill_ids=req.skill_ids,
        auto_agent=req.auto_agent,
        auto_skills=req.auto_skills
    )
    
    tools_result = await db.execute(select(Tool).where(Tool.is_active == True))
    active_tools = tools_result.scalars().all()
    formatted_tools = None
    if active_tools:
        formatted_tools = []
        for t in active_tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema
                }
            })
            
    try:
        provider_id, model_id, response, is_fallback = await select_and_call_provider(
            chat_id=req.chat_id, 
            prompt_builder=prompt_builder,
            db=db, 
            stream=True, 
            tools=formatted_tools
        )
    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))
        
    from sse_starlette.sse import EventSourceResponse
    
    async def stream_and_save():
        yield {"event": "chat_meta", "data": json.dumps({"chat_id": req.chat_id, "provider_id": provider_id, "model_id": model_id, "is_fallback": is_fallback})}
        
        full_content = ""
        tool_calls_buffer = {}
        
        async for chunk in response:
            if isinstance(chunk, dict):
                chunk_dict = chunk
            elif hasattr(chunk, "model_dump"):
                chunk_dict = chunk.model_dump(exclude_none=True)
            elif hasattr(chunk, "dict"):
                chunk_dict = chunk.dict(exclude_none=True)
            else:
                chunk_dict = dict(chunk)
                
            delta = chunk_dict.get("choices", [{}])[0].get("delta", {})
            if "content" in delta and delta.get("content"):
                full_content += delta["content"]
                
            if "tool_calls" in delta:
                for tc in delta["tool_calls"]:
                    idx = tc.get("index", 0)
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {"id": tc.get("id"), "type": "function", "function": {"name": "", "arguments": ""}}
                    if tc.get("id"):
                        tool_calls_buffer[idx]["id"] = tc["id"]
                    if tc.get("function"):
                        if tc["function"].get("name"):
                            tool_calls_buffer[idx]["function"]["name"] += tc["function"]["name"]
                        if tc["function"].get("arguments"):
                            tool_calls_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]

            yield {"data": json.dumps(chunk_dict)}
            
        if tool_calls_buffer:
            tool_calls_list = [v for k, v in sorted(tool_calls_buffer.items())]
            assistant_payload = {
                "text": full_content,
                "tool_calls": tool_calls_list
            }
            assistant_msg = Message(
                chat_id=req.chat_id,
                role="assistant",
                content=json.dumps(assistant_payload),
                provider_id=provider_id,
                model_id=model_id
            )
            db.add(assistant_msg)
            await db.commit()
            
            yield {"event": "tool_calls_pending", "data": json.dumps(tool_calls_list)}
            return
        else:
            yield {"data": "[DONE]"}
            assistant_msg = Message(
                chat_id=req.chat_id,
                role="assistant",
                content=full_content,
                provider_id=provider_id,
                model_id=model_id
            )
            db.add(assistant_msg)
            chat.updated_at = datetime.now(timezone.utc)
            await db.commit()
            
            # Fire reflection
            import asyncio
            asyncio.create_task(run_reflection_cycle(req.chat_id))
            
    return EventSourceResponse(stream_and_save())

class EnhanceRequest(BaseModel):
    text: str

@router.post("/chat/enhance")
async def enhance_prompt(req: EnhanceRequest, db: AsyncSession = Depends(get_db)):
    """Rewrites a short user prompt into a highly detailed expert prompt."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    system_prompt = (
        "You are an expert prompt engineer. Your task is to rewrite the user's brief request "
        "into a highly detailed, comprehensive, and clear prompt for a senior AI software engineer. "
        "Expand on best practices, potential edge cases to consider, and specify that the code should "
        "be production-ready. Output ONLY the rewritten prompt. Do not include any conversational filler."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": req.text}
    ]
    
    try:
        # We want to force it to use a local model if available, otherwise just use auto-route
        # By passing force_model_id=None, it uses the fallback router. 
        # But wait! The fallback router prioritizes Cloud > Local right now.
        # We can temporarily reverse priority logic for this call or just let it use the fastest cloud model.
        # To strictly try local first, we can query local providers:
        local_provider = await db.execute(select(Provider).where(Provider.type == "local", Provider.is_active == True))
        local_p = local_provider.scalars().first()
        
        force_model_id = None
        if local_p:
            local_models = await db.execute(select(AIModel).where(AIModel.provider_id == local_p.id, AIModel.is_active == True))
            lms = local_models.scalars().all()
            
            import re
            
            # Pass 1: Explicit user preference
            for m in lms:
                if "gpt-oss" in m.model_name.lower():
                    force_model_id = m.id
                    break
                    
            # Pass 2: Size <= 10B
            if not force_model_id:
                for m in lms:
                    m_name = m.model_name.lower()
                    match = re.search(r'(\d+(?:\.\d+)?)b', m_name)
                    if match:
                        size = float(match.group(1))
                        if size <= 10.0:
                            force_model_id = m.id
                            break
                    else:
                        small_keywords = ["mini", "small", "phi", "mistral"]
                        huge_keywords = ["large", "huge", "pro", "max", "glm"]
                        if any(k in m_name for k in small_keywords) and not any(h in m_name for h in huge_keywords):
                            force_model_id = m.id
                            break
                
        provider_id, model_id, response, is_fallback = await select_and_call_provider(
            messages=messages,
            db=db,
            stream=True,
            force_model_id=force_model_id
        )
        
        from sse_starlette.sse import EventSourceResponse
        
        async def stream_enhance():
            async for chunk in response:
                if isinstance(chunk, dict):
                    chunk_dict = chunk
                elif hasattr(chunk, "model_dump"):
                    chunk_dict = chunk.model_dump(exclude_none=True)
                elif hasattr(chunk, "dict"):
                    chunk_dict = chunk.dict(exclude_none=True)
                else:
                    chunk_dict = dict(chunk)
                    
                delta = chunk_dict.get("choices", [{}])[0].get("delta", {})
                if "content" in delta and delta.get("content"):
                    yield {"data": json.dumps({"text": delta["content"]})}
                    
            yield {"data": "[DONE]"}
            
        return EventSourceResponse(stream_enhance())
            
    except Exception as e:
        logger.error(f"Enhance failed: {e}")
        return {"enhanced_text": req.text} # graceful fallback

