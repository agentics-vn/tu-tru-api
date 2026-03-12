"""
auth.py — API key authentication and rate limiting middleware.

Validates X-API-Key header and enforces per-key daily rate limits.
Keys are validated against hashed values (SHA-256).

When Redis is unavailable, rate limiting is skipped (fail-open for auth,
fail-open for rate limiting). This allows the API to function without
Redis during development.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("bat_tu_api.auth")

# Paths that skip authentication
_PUBLIC_PATHS: frozenset[str] = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})

# Daily rate limit per key (BASIC plan)
RATE_LIMIT_DAILY = 100

# In-memory key store for development (hash → plan).
# Production should use DB lookup.
# Seed with BATTU_API_KEYS env var: comma-separated "key:plan" pairs.
_KEY_STORE: dict[str, str] = {}

# In-memory rate limit counters (fallback when Redis unavailable)
# Structure: { key_hash: { "count": int, "reset_at": float } }
_RATE_COUNTERS: dict[str, dict] = {}


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def _load_keys_from_env() -> None:
    """Load API keys from BATTU_API_KEYS env var for dev/testing."""
    raw = os.environ.get("BATTU_API_KEYS", "")
    if not raw:
        return
    for entry in raw.split(","):
        entry = entry.strip()
        if ":" in entry:
            key, plan = entry.split(":", 1)
        else:
            key, plan = entry, "BASIC"
        _KEY_STORE[_hash_key(key.strip())] = plan.strip()


def _validate_key(api_key: str) -> Optional[str]:
    """Validate API key, return plan name or None if invalid."""
    if not _KEY_STORE:
        _load_keys_from_env()

    # Dev mode: if no keys configured, accept any non-empty key
    if not _KEY_STORE:
        if os.environ.get("NODE_ENV", "development") == "development":
            return "BASIC"
        return None

    key_hash = _hash_key(api_key)
    return _KEY_STORE.get(key_hash)


def _check_rate_limit(key_hash: str) -> tuple[bool, int, int]:
    """
    Check in-memory rate limit for a key.

    Returns: (allowed, remaining, reset_at_unix)
    """
    now = time.time()
    # Calculate next midnight UTC
    import calendar
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()
    tomorrow = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    tomorrow_ts = int(calendar.timegm(tomorrow.timetuple())) + 86400

    counter = _RATE_COUNTERS.get(key_hash)
    if counter is None or now >= counter["reset_at"]:
        _RATE_COUNTERS[key_hash] = {"count": 1, "reset_at": tomorrow_ts}
        return True, RATE_LIMIT_DAILY - 1, tomorrow_ts

    if counter["count"] >= RATE_LIMIT_DAILY:
        return False, 0, int(counter["reset_at"])

    counter["count"] += 1
    remaining = RATE_LIMIT_DAILY - counter["count"]
    return True, remaining, int(counter["reset_at"])


class AuthMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for API key auth + rate limiting."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        # Extract API key
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error_code": "UNAUTHORIZED",
                    "message": "Missing X-API-Key header",
                },
            )

        # Validate key
        plan = _validate_key(api_key)
        if plan is None:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error_code": "UNAUTHORIZED",
                    "message": "Invalid API key",
                },
            )

        # Rate limiting
        key_hash = _hash_key(api_key)
        allowed, remaining, reset_at = _check_rate_limit(key_hash)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error_code": "RATE_LIMITED",
                    "message": f"Rate limit exceeded. Resets at {reset_at}.",
                },
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                },
            )

        # Attach auth info to request state
        request.state.api_plan = plan
        request.state.api_key_hash = key_hash

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response
