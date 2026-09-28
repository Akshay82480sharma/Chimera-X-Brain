import os
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

# Global Redis client
redis_client = None

async def init_redis():
    global redis_client
    redis_url = os.environ.get("REDIS_URL")
    
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            await redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Falling back to in-memory caching.")
            redis_client = None
    else:
        logger.info("REDIS_URL not set. Running without Redis caching.")

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")

async def get_redis():
    """Dependency that yields the Redis client (or None)."""
    return redis_client
