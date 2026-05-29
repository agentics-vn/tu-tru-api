"""Profile persistence — Redis when available, in-memory fallback (P2-05)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from cache.redis import get_redis_client

logger = logging.getLogger("bat_tu_api.profile_store")

PROFILE_PREFIX = "profile:"
PROFILE_TTL_SECONDS = 90 * 24 * 3600
_MAX_MEMORY_PROFILES = 10_000

_memory: dict[str, dict[str, Any]] = {}


def get_profile(profile_id: str) -> Optional[dict[str, Any]]:
    client = get_redis_client()
    if client is not None:
        try:
            raw = client.get(f"{PROFILE_PREFIX}{profile_id}")
            if raw is not None:
                return json.loads(raw)
        except Exception:
            logger.debug("Redis profile get failed for %s", profile_id)
    return _memory.get(profile_id)


def save_profile(profile_id: str, data: dict[str, Any]) -> None:
    client = get_redis_client()
    if client is not None:
        try:
            client.setex(
                f"{PROFILE_PREFIX}{profile_id}",
                PROFILE_TTL_SECONDS,
                json.dumps(data, ensure_ascii=False),
            )
            return
        except Exception:
            logger.debug("Redis profile set failed for %s", profile_id)

    if profile_id not in _memory and len(_memory) >= _MAX_MEMORY_PROFILES:
        oldest = next(iter(_memory))
        del _memory[oldest]

    _memory[profile_id] = data


def memory_profile_count() -> int:
    return len(_memory)
