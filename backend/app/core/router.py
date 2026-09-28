"""Model router with fallback capabilities.

This module handles selecting the best provider and model for a given request,
automatically falling back to the next provider on quotas/rate limits.
"""

from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.models import Provider, AIModel, RouterLog
from app.core.litellm_proxy import call_litellm
import litellm
import httpx

logger = logging.getLogger(__name__)


async def classify_task(messages: list[dict], db: AsyncSession) -> str:
    """Classifies the conversation into a task type: chat, code, extraction, vision"""
    if not messages:
        return "chat"
        
    # Check for vision payloads first
    for msg in messages:
        if isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if part.get("type") == "image_url":
                    return "vision"
    
    last_msg = messages[-1].get("content", "")
    last_msg_lower = last_msg.lower()
    
    # 1. Try semantic classification using a small local model
    try:
        local_p = (await db.execute(select(Provider).where(Provider.type == "local", Provider.is_active == True))).scalars().first()
        if local_p:
            local_models = (await db.execute(select(AIModel).where(AIModel.provider_id == local_p.id, AIModel.is_active == True))).scalars().all()
            
            import re
            
            small_model = None
            # Pass 1: Try to find a very small model (<= 3.5B) for fastest routing
            for m in local_models:
                m_name = m.model_name.lower()
                match = re.search(r'(\d+(?:\.\d+)?)b', m_name)
                if match:
                    size = float(match.group(1))
                    if size <= 3.5:
                        small_model = m
                        break
                        
            # Pass 2: Fallback to <= 8.5B or keyword matching
            if not small_model:
                for m in local_models:
                    m_name = m.model_name.lower()
                    match = re.search(r'(\d+(?:\.\d+)?)b', m_name)
                    if match:
                        size = float(match.group(1))
                        if size <= 8.5:
                            small_model = m
                            break
                    else:
                        small_keywords = ["mini", "small", "phi", "mistral", "qwen", "llama"]
                        huge_keywords = ["large", "huge", "pro", "max", "glm", "oss-20b"]
                        if any(k in m_name for k in small_keywords) and not any(h in m_name for h in huge_keywords):
                            small_model = m
                            break
            
            if small_model:
                provider_prefix = "openai/" if local_p.slug in ["lm-studio", "ollama"] else f"{local_p.slug}/"
                litellm_model = f"{provider_prefix}{small_model.model_name}"
                
                response = await litellm.acompletion(
                    model=litellm_model,
                    messages=[
                        {"role": "system", "content": "You are a semantic router. Classify the user's intent into EXACTLY ONE of these categories: 'code', 'extraction', 'chat'. Respond with only the category word in lowercase."},
                        {"role": "user", "content": last_msg[:500]}
                    ],
                    api_base=local_p.base_url,
                    api_key="dummy-key",  # Local models don't need real keys
                    max_tokens=10,
                    temperature=0.0,
                    timeout=5.0
                )
                category = response.choices[0].message.content.strip().lower()
                if category in ["code", "extraction", "chat"]:
                    return category
    except Exception as e:
        logger.warning(f"Local semantic routing failed, falling back to keywords: {e}")


    # 2. Keyword fallback
    if any(k in last_msg_lower for k in ["code", "debug", "python", "javascript", "react", "function", "api"]):
        return "code"
    if any(k in last_msg_lower for k in ["extract", "summarize", "json", "parse", "format"]):
        return "extraction"
        
    return "chat"


async def select_and_call_provider(
    messages: list[dict],
    db: AsyncSession,
    stream: bool = False,
    tools: list = None,
    force_model_id: int = None,
) -> tuple[int, int, any, bool]:
    """Select the best provider and call it, falling back if rate limited.
    
    Returns:
        Tuple of (provider_id, model_id, response_or_stream, is_fallback)
    """
    task_type = "chat"
    if not force_model_id:
        task_type = await classify_task(messages, db)
    
    # 1. Query active providers, ordered by priority
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Provider)
        .where(Provider.is_active == True)
    )
    providers = result.scalars().all()
    
    if not providers:
        raise Exception("No active providers configured.")
        
    # --- MANUAL OVERRIDE (force_model_id) ---
    if force_model_id:
        result = await db.execute(select(AIModel).where(AIModel.id == force_model_id))
        manual_model = result.scalars().first()
        if not manual_model:
            raise Exception(f"Model ID {force_model_id} not found.")
            
        manual_provider = next((p for p in providers if p.id == manual_model.provider_id), None)
        if not manual_provider:
            raise Exception(f"Provider for model {force_model_id} is not active or found.")
            
        ordered_providers = [manual_provider]
    else:
        # 1.5. Check resets and soft limits
        healthy_providers = []
        near_limit_providers = []
        
        for provider in providers:
            # Reset quota if it's a new day
            if provider.last_reset_at and provider.last_reset_at.date() < now.date():
                provider.daily_quota_used = 0
                provider.last_reset_at = now
                
            if provider.daily_quota_limit and provider.daily_quota_used >= (provider.daily_quota_limit * 0.9):
                near_limit_providers.append(provider)
            else:
                healthy_providers.append(provider)
                
        # Sort each group by priority
        healthy_providers.sort(key=lambda p: p.priority)
        near_limit_providers.sort(key=lambda p: p.priority)
        
        # Try healthy first, then near_limit
        ordered_providers = healthy_providers + near_limit_providers
        
    skipped_reasons = []
        
    provider_attempt_count = 0
    model_attempt_count = 0

    # Loop through providers for fallback
    for provider in ordered_providers:
        provider_attempt_count += 1
        # 2. Skip if currently rate limited and still in cooldown window
        if provider.is_rate_limited and provider.rate_limit_reset_at:
            # Ensure both are timezone aware for comparison
            # SQLite datetime retrieval can sometimes be naive if not configured properly,
            # but SQLAlchemy handles it. Let's make sure:
            reset_at = provider.rate_limit_reset_at
            if reset_at.tzinfo is None:
                reset_at = reset_at.replace(tzinfo=timezone.utc)
                
            if reset_at > now:
                logger.info(f"Skipping {provider.name} (rate limited until {reset_at})")
                skipped_reasons.append(f"- {provider.name}: On rate limit cooldown until {reset_at.strftime('%H:%M:%S UTC')}")
                continue
            else:
                # Cooldown expired, clear rate limit
                provider.is_rate_limited = False
                provider.rate_limit_reset_at = None
                await db.commit()
                
        # Get models for this provider
        model_result = await db.execute(
            select(AIModel)
            .where(AIModel.provider_id == provider.id, AIModel.is_active == True)
        )
        models = model_result.scalars().all()
        
        if not models:
            skipped_reasons.append(f"- {provider.name}: No active models added. (Go to Model Manager and add a model)")
            continue
            
        # 3. Task-based model selection (ordered by preference)
        target_models = []
        if task_type == "vision":
            vision_keywords = ["qwen", "gemma"]
            target_models = [m for m in models if any(k in m.model_name.lower() for k in vision_keywords)]
            # If no specific vision models found in this provider, fallback to all models
            if not target_models:
                target_models = models
        elif force_model_id:
            target_models = [m for m in models if m.id == force_model_id]
        else:
            for m in models:
                if m.task_tags and task_type in m.task_tags:
                    target_models.append(m)
            for m in models:
                if m not in target_models:
                    target_models.append(m)
                
        # Try models in order of preference
        for selected_model in target_models:
            model_attempt_count += 1
            litellm_kwargs = {}
            if provider.base_url:
                litellm_kwargs["api_base"] = provider.base_url
            if provider.api_key:
                litellm_kwargs["api_key"] = provider.api_key
            if tools:
                litellm_kwargs["tools"] = tools
                
            try:
                model_name = selected_model.model_name
                
                # Auto-prefix based on known cloud provider slugs
                known_prefixes = ["openrouter", "gemini", "perplexity", "huggingface", "cerebras"]
                for p_slug in known_prefixes:
                    if provider.slug.startswith(p_slug) and not model_name.startswith(f"{p_slug}/"):
                        model_name = f"{p_slug}/{model_name}"
                        
                if provider.type == "local" or provider.base_url:
                    if provider.slug.startswith("ollama"):
                        if not model_name.startswith("ollama/"):
                            model_name = f"ollama/{model_name}"
                    elif provider.slug.startswith("lm-studio"):
                        if not model_name.startswith("openai/"):
                            model_name = f"openai/{model_name}"
                    elif not any(model_name.startswith(f"{px}/") for px in known_prefixes + ["openai", "anthropic", "google"]):
                        model_name = f"openai/{model_name}"
                        
                # OpenAI SDK requires *some* API key even for local/custom endpoints
                if "api_key" not in litellm_kwargs and model_name.startswith("openai/"):
                    litellm_kwargs["api_key"] = "dummy-key-for-local"
                    
                # --- LM STUDIO JIT AUTO-LOADING ---
                if provider.slug.startswith("lm-studio") and provider.base_url:
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            # Check currently loaded models
                            res = await client.get(f"{provider.base_url.rstrip('/')}/models")
                            if res.status_code == 200:
                                data = res.json()
                                loaded_models = [m.get("id") for m in data.get("data", [])]
                                
                                # If our target model is not loaded, send a load request
                                if selected_model.model_name not in loaded_models:
                                    logger.info(f"Model {selected_model.model_name} not loaded in LM Studio. Triggering JIT load...")
                                    load_url = provider.base_url.rstrip('/').replace('/v1', '/api/v1') + "/models/load"
                                    load_payload = {"model": selected_model.model_name}
                                    
                                    # Loading large models can take time, use a high timeout
                                    async with httpx.AsyncClient(timeout=120.0) as long_client:
                                        load_res = await long_client.post(load_url, json=load_payload)
                                        if load_res.status_code == 200:
                                            logger.info(f"Successfully loaded {selected_model.model_name} into LM Studio.")
                                        else:
                                            logger.warning(f"Failed to JIT load model: {load_res.status_code} {load_res.text}")
                    except Exception as e:
                        logger.warning(f"Error during LM Studio JIT check/load: {e}")
                # ----------------------------------
    
                logger.info(f"Attempting {provider.name} with model {model_name}")
                start_time = datetime.now(timezone.utc)
                response = await call_litellm(
                    messages=messages,
                    model=model_name,
                    stream=stream,
                    **litellm_kwargs
                )
                
                latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                
                # On Success:
                is_fallback = (provider_attempt_count > 1) or (model_attempt_count > 1)

                provider.daily_quota_used = (provider.daily_quota_used or 0) + 1
                if not provider.last_reset_at:
                    provider.last_reset_at = now
                    
                log_entry = RouterLog(
                    provider_to_id=provider.id,
                    success=True,
                    latency_ms=latency_ms,
                    task_type=task_type
                )
                db.add(log_entry)
                await db.commit()
                
                return provider.id, selected_model.id, response, is_fallback
                
            except Exception as e:
                latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                error_str = str(e).lower()
                last_error = str(e)
                logger.error(f"Provider {provider.name}, Model {selected_model.model_name} failed: {e}")
                
                # 4.a On Memory/Size error -> try next model in this provider
                if "insufficient system resources" in error_str or "memory" in error_str or "oom" in error_str or "too large" in error_str:
                    logger.warning(f"Model {selected_model.model_name} is too large or out of memory. Trying next model...")
                    skipped_reasons.append(f"- {provider.name}: Model '{selected_model.model_name}' failed to load (Insufficient Memory/Resources).")
                    continue # Try the next model!
                    
                # 4.b On Model Not Found error -> try next model in this provider
                if "not found" in error_str or "does not exist" in error_str or "not_found_error" in error_str:
                    logger.warning(f"Model {selected_model.model_name} not found. Trying next model...")
                    skipped_reasons.append(f"- {provider.name}: Model '{selected_model.model_name}' was not found on the server.")
                    continue # Try the next model!
                
                # 5. On 429 / Quota Error -> Fallback to NEXT PROVIDER
                if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                    logger.warning(f"Rate limit hit on {provider.name}. Falling back to next provider...")
                    provider.is_rate_limited = True
                    provider.rate_limit_reset_at = now + timedelta(seconds=60) # Default 60s cooldown
                    provider.last_error_at = now
                    
                    log_entry = RouterLog(
                        provider_to_id=provider.id,
                        success=False,
                        latency_ms=latency_ms,
                        reason="quota_exceeded",
                        task_type=task_type
                    )
                    db.add(log_entry)
                    await db.commit()
                    break # Break model loop, continue to next provider
                
                # For other errors (e.g. 500, network issues), we also fallback to NEXT PROVIDER
                logger.warning(f"Error on {provider.name}. Falling back to next provider...")
                provider.last_error_at = now
                
                log_entry = RouterLog(
                    provider_to_id=provider.id,
                    success=False,
                    latency_ms=latency_ms,
                    reason=error_str[:100],
                    task_type=task_type
                )
                db.add(log_entry)
                await db.commit()
                break # Break model loop, continue to next provider
            
    # 6. If all providers exhausted
    if 'last_error' in locals():
        error_msg = f"All providers failed or are rate limited.\n\nLast error:\n{last_error}"
    elif skipped_reasons:
        error_msg = f"All providers failed or are rate limited.\n\nSkipped providers:\n" + "\n".join(skipped_reasons)
    else:
        error_msg = "All providers failed or are rate limited."
        
    raise Exception(error_msg)
