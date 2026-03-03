"""Simple in-memory cache for rendered public pages."""

import time
from functools import wraps
from typing import Any

_cache: dict[str, tuple[Any, float]] = {}
DEFAULT_TTL = 300  # 5 minutes


def cache_get(key: str) -> Any | None:
    """Get value from cache. Returns None if expired or not found."""
    if key in _cache:
        value, expires = _cache[key]
        if time.time() < expires:
            return value
        del _cache[key]
    return None


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    """Set a value in cache with TTL."""
    _cache[key] = (value, time.time() + ttl)


def cache_delete(key: str):
    """Delete a specific cache key."""
    _cache.pop(key, None)


def cache_clear():
    """Clear entire cache."""
    _cache.clear()


def cache_delete_pattern(pattern: str):
    """Delete all cache keys that start with the given pattern."""
    keys_to_delete = [k for k in _cache if k.startswith(pattern)]
    for k in keys_to_delete:
        del _cache[k]


def cached(prefix: str, ttl: int = DEFAULT_TTL):
    """Decorator to cache async function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from prefix + args
            key_parts = [prefix] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = ":".join(key_parts)

            result = cache_get(key)
            if result is not None:
                return result

            result = await func(*args, **kwargs)
            cache_set(key, result, ttl)
            return result
        return wrapper
    return decorator
