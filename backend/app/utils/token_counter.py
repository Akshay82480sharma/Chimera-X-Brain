import logging
try:
    import tiktoken
except ImportError:
    tiktoken = None

logger = logging.getLogger(__name__)

def get_token_count(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Returns the number of tokens in a text string.
    Falls back to a rough character-based estimate if tiktoken is not installed.
    """
    if not text:
        return 0
        
    if tiktoken:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to standard encoding if model not found
            encoding = tiktoken.get_encoding("cl100k_base")
            
        try:
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error calculating token count with tiktoken: {e}")
            
    # Rough fallback: ~4 characters per token
    return len(text) // 4

def get_messages_token_count(messages: list[dict], model: str = "gpt-3.5-turbo") -> int:
    """
    Returns the number of tokens used by a list of messages.
    Includes overhead for message roles.
    """
    if not messages:
        return 0
        
    num_tokens = 0
    for message in messages:
        # 4 tokens overhead per message
        num_tokens += 4
        for key, value in message.items():
            if isinstance(value, str):
                num_tokens += get_token_count(value, model)
            elif isinstance(value, list) or isinstance(value, dict):
                import json
                num_tokens += get_token_count(json.dumps(value), model)
                
    # 2 tokens overhead for the final reply primer
    num_tokens += 2
    return num_tokens
