"""Redis cache layer for WAYOS speed strategy.

Provides simple get/set/invalidate with JSON serialization and TTL.
Falls back gracefully if Redis is unavailable.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis():
    """Get or create Redis client. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis connected at %s", redis_url)
        return _redis_client
    except Exception:
        logger.warning("Redis unavailable at %s — caching disabled", redis_url)
        _redis_client = None
        return None


def cache_get(key: str) -> Optional[dict]:
    """Get cached value. Returns None on miss or error."""
    r = get_redis()
    if r is None:
        return None
    try:
        val = r.get(f"wayos:{key}")
        if val:
            return json.loads(val)
    except Exception:
        logger.debug("Cache get failed for %s", key)
    return None


def cache_set(key: str, value: dict, ttl: int = 300) -> bool:
    """Set cached value with TTL in seconds. Returns True on success."""
    r = get_redis()
    if r is None:
        return False
    try:
        r.setex(f"wayos:{key}", ttl, json.dumps(value, default=str))
        return True
    except Exception:
        logger.debug("Cache set failed for %s", key)
        return False


def cache_invalidate(key: str) -> bool:
    """Delete cached value. Returns True on success."""
    r = get_redis()
    if r is None:
        return False
    try:
        r.delete(f"wayos:{key}")
        return True
    except Exception:
        logger.debug("Cache invalidate failed for %s", key)
        return False


def reset_redis():
    """Reset the Redis client (for testing)."""
    global _redis_client
    _redis_client = None
