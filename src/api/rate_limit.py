"""Rate-limit headers (Direction C P3-04) — Redis when available, bounded in-memory fallback."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from cache.redis import get_redis_client

_MAX_MEMORY_KEYS = 10_000
_REDIS_KEY_TTL = 120


def _limit_per_minute() -> int:
    raw = os.environ.get("RATE_LIMIT_PER_MINUTE", "300")
    try:
        return max(1, int(raw))
    except ValueError:
        return 300


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Attach X-RateLimit-* headers; return 429 when limit exceeded."""

    def __init__(self, app, limit_per_minute: int | None = None) -> None:
        super().__init__(app)
        self._limit = limit_per_minute or _limit_per_minute()
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._last_seen: dict[str, float] = {}

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _redis_hit_count(self, key: str) -> int | None:
        client = get_redis_client()
        if client is None:
            return None
        bucket = int(time.time() // 60)
        rk = f"ratelimit:{key}:{bucket}"
        try:
            raw = client.get(rk)
            return int(raw) if raw is not None else 0
        except Exception:
            return None

    def _redis_record_hit(self, key: str) -> None:
        client = get_redis_client()
        if client is None:
            return
        bucket = int(time.time() // 60)
        rk = f"ratelimit:{key}:{bucket}"
        try:
            count = client.incr(rk)
            if count == 1:
                client.expire(rk, _REDIS_KEY_TTL)
        except Exception:
            pass

    def _memory_hit_count(self, key: str) -> int:
        now = time.time()
        window_start = now - 60.0
        hits = [t for t in self._buckets[key] if t >= window_start]
        self._buckets[key] = hits
        return len(hits)

    def _memory_record_hit(self, key: str) -> None:
        now = time.time()
        if key not in self._buckets and len(self._buckets) >= _MAX_MEMORY_KEYS:
            lru_key = min(self._last_seen, key=lambda k: self._last_seen[k])
            self._buckets.pop(lru_key, None)
            self._last_seen.pop(lru_key, None)
        self._buckets[key].append(now)
        self._last_seen[key] = now

    def _hit_count(self, key: str) -> int:
        redis_count = self._redis_hit_count(key)
        if redis_count is not None:
            return redis_count
        return self._memory_hit_count(key)

    def _record_hit(self, key: str) -> None:
        if get_redis_client() is not None:
            self._redis_record_hit(key)
        else:
            self._memory_record_hit(key)

    def _remaining(self, key: str) -> int:
        return max(0, self._limit - self._hit_count(key))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/health":
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self._limit)
            response.headers["X-RateLimit-Remaining"] = str(self._limit)
            return response

        key = self._client_key(request)
        remaining_before = self._remaining(key)

        if remaining_before <= 0:
            from api.errors import error_response

            resp = error_response(
                429,
                "RATE_LIMITED",
                message_vi="Quá nhiều yêu cầu. Vui lòng thử lại sau.",
                message_en="Too many requests. Please try again later.",
            )
            resp.headers["X-RateLimit-Limit"] = str(self._limit)
            resp.headers["X-RateLimit-Remaining"] = "0"
            return resp

        self._record_hit(key)
        remaining_after = self._remaining(key)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining_after)
        return response
