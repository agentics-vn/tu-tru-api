"""
redis.py — Redis cache for Layer 1 day info.

Cache key format: layer1:{YYYY-MM-DD}
TTL: 86400 seconds (1 day) — per algorithm.md §11.

Falls back gracefully when Redis is unavailable (returns None on get,
silently drops on set). This lets the API work without Redis in dev.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger("bat_tu_api.cache")

LAYER1_TTL = 86400  # 1 day in seconds

# Redis client — lazy-initialized
_redis_client = None
_redis_available: Optional[bool] = None


def _get_client():
    """Get or create Redis client. Returns None if Redis unavailable."""
    global _redis_client, _redis_available

    if _redis_available is False:
        return None

    if _redis_client is not None:
        return _redis_client

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        import redis
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected: %s", redis_url)
        return _redis_client
    except Exception:
        _redis_available = False
        logger.warning("Redis unavailable at %s — caching disabled", redis_url)
        return None


def get_day_info_cached(iso_date: str) -> Optional[dict]:
    """
    Get cached Layer 1 day info.

    Args:
        iso_date: 'YYYY-MM-DD'

    Returns:
        Cached dict or None if not cached / Redis unavailable.
    """
    client = _get_client()
    if client is None:
        return None

    key = f"layer1:{iso_date}"
    try:
        raw = client.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception:
        logger.debug("Redis get failed for %s", key)
    return None


def set_day_info_cached(iso_date: str, day_info: dict) -> None:
    """
    Cache Layer 1 day info.

    Args:
        iso_date: 'YYYY-MM-DD'
        day_info: dict from get_day_info()
    """
    client = _get_client()
    if client is None:
        return

    key = f"layer1:{iso_date}"
    try:
        client.setex(key, LAYER1_TTL, json.dumps(day_info, ensure_ascii=False))
    except Exception:
        logger.debug("Redis set failed for %s", key)


def get_month_info_cached(year: int, month: int) -> Optional[list[dict]]:
    """Get cached month info."""
    client = _get_client()
    if client is None:
        return None

    key = f"layer1:{year}-{month:02d}"
    try:
        raw = client.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception:
        logger.debug("Redis get failed for %s", key)
    return None


def set_month_info_cached(year: int, month: int, month_info: list[dict]) -> None:
    """Cache month info."""
    client = _get_client()
    if client is None:
        return

    key = f"layer1:{year}-{month:02d}"
    try:
        client.setex(key, LAYER1_TTL, json.dumps(month_info, ensure_ascii=False))
    except Exception:
        logger.debug("Redis set failed for %s", key)


def invalidate_cache() -> None:
    """Flush all layer1 cache keys using SCAN (O(1) per iteration, non-blocking)."""
    client = _get_client()
    if client is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor, match="layer1:*", count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        logger.debug("Redis invalidate failed")
