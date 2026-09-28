"""LiteLLM proxy layer — the disposable 'mouth' of Chimera-X.

This module handles raw LiteLLM API calls (streaming + non-streaming).
It is provider-agnostic: which provider to call is decided by the router,
not by this module.

Extracted from ai-model-router/backend/api/openai_compat.py during Phase 1
consolidation.
"""

import json
from typing import Any, Optional

import litellm
from sse_starlette.sse import EventSourceResponse


async def call_litellm(
    messages: list[dict],
    model: str,
    stream: bool = False,
    **kwargs: Any,
) -> Any:
    """Make a completion call via LiteLLM.
    
    Args:
        messages: The message list (from build_context).
        model: The LiteLLM model identifier (e.g. "gpt-4o", "claude-3-5-sonnet-20240620").
        stream: Whether to stream the response.
        **kwargs: Additional LiteLLM params (temperature, max_tokens, etc.).
    
    Returns:
        If stream=False: the full response dict.
        If stream=True: an EventSourceResponse for SSE streaming.
    """
    call_params = {
        "model": model,
        "messages": messages,
        "stream": stream,
        **kwargs,
    }

    if stream:
        return await litellm.acompletion(**call_params)
    else:
        response = await litellm.acompletion(**call_params)
        return response.model_dump(exclude_none=True)
