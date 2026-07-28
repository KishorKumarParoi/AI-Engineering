import hashlib
import json
import re
from typing import Any, Dict, Optional
import logfire
from app.config import settings

# Global redis client cache reference
_redis_client = None


def _get_redis():
    """Lazy-initialize Redis client for caching."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        from limits.storage import RedisStorage

        storage = RedisStorage(settings.redis_url)
        if storage.check() and storage.storage.ping():
            _redis_client = storage.storage
            return _redis_client
    except Exception as e:
        logfire.warning(f"⚠️ Response cache Redis connection unavailable: {e}")

    return None


def normalize_query(query: str) -> str:
    """Normalize query text by lowercasing, stripping punctuation, and collapsing whitespace."""
    if not query:
        return ""
    # Lowercase & collapse multiple spaces
    normalized = query.strip().lower()
    normalized = re.sub(r"[?\!.,;:]+$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def get_cache_key(query: str) -> str:
    """Generate SHA256 cache key from normalized query string."""
    norm = normalize_query(query)
    query_hash = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return f"rag:query_cache:{query_hash}"


def get_cached_response(query: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached response for a query if available."""
    r = _get_redis()
    if r is None:
        return None

    try:
        key = get_cache_key(query)
        cached_data = r.get(key)
        if cached_data:
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode("utf-8")
            data = json.loads(cached_data)
            logfire.info("⚡ Response Cache Hit", query=query)
            return data
    except Exception as e:
        logfire.warning(f"⚠️ Cache read error: {e}")

    return None


def set_cached_response(query: str, response_data: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
    """Cache the response dictionary for a query with TTL."""
    r = _get_redis()
    if r is None:
        return False

    try:
        key = get_cache_key(query)
        payload = json.dumps(response_data)
        r.setex(key, ttl_seconds, payload)
        logfire.info("💾 Cached response for query", query=query, ttl=ttl_seconds)
        return True
    except Exception as e:
        logfire.warning(f"⚠️ Cache write error: {e}")
        return False


def clear_query_cache() -> bool:
    """Clear all query cache entries in Redis."""
    r = _get_redis()
    if r is None:
        return False

    try:
        keys = r.keys("rag:query_cache:*")
        if keys:
            r.delete(*keys)
        return True
    except Exception as e:
        logfire.warning(f"⚠️ Cache clear error: {e}")
        return False
