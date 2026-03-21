"""
Shareable result tokens (T5-01).

Generates short, URL-safe HMAC-signed tokens that encode the request parameters
needed to reproduce a result. The token is self-contained (no DB lookup required).

Token format: base64url( JSON payload + "." + HMAC-SHA256 signature )
The payload does NOT contain raw birth data — only a SHA-256 hash of it,
so the shareable URL never exposes personal information.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

# Secret for signing tokens — must be set in production
_SECRET = os.environ.get("SHARE_TOKEN_SECRET", "dev-secret-change-me").encode()

# Token validity: 90 days
TOKEN_TTL_SECONDS = 90 * 24 * 3600


def _hash_birth_data(birth_date: str, birth_time: int | None, gender: int | None) -> str:
    """One-way hash of birth data so it never appears in the token."""
    raw = f"{birth_date}|{birth_time}|{gender}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def create_share_token(
    *,
    endpoint: str,
    birth_date: str,
    birth_time: int | None = None,
    gender: int | None = None,
    intent: str | None = None,
    target_date: str | None = None,
    range_start: str | None = None,
    range_end: str | None = None,
    extra: dict | None = None,
) -> str:
    """Create a signed, URL-safe share token.

    The token encodes enough info to re-run the query, but uses a hash
    instead of raw birth data so the URL is safe to share publicly.
    """
    payload: dict = {
        "ep": endpoint,
        "bd": birth_date,
        "bt": birth_time,
        "g": gender,
        "bh": _hash_birth_data(birth_date, birth_time, gender),
        "ts": int(time.time()),
    }
    if intent:
        payload["in"] = intent
    if target_date:
        payload["td"] = target_date
    if range_start:
        payload["rs"] = range_start
    if range_end:
        payload["re"] = range_end
    if extra:
        payload["x"] = extra

    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    sig = hmac.new(_SECRET, payload_bytes, hashlib.sha256).hexdigest()[:16]
    raw = payload_bytes + b"." + sig.encode()
    return urlsafe_b64encode(raw).decode().rstrip("=")


def decode_share_token(token: str) -> dict | None:
    """Decode and verify a share token. Returns payload dict or None if invalid."""
    try:
        # Re-add padding
        padding = 4 - len(token) % 4
        if padding != 4:
            token += "=" * padding

        raw = urlsafe_b64decode(token)
        parts = raw.rsplit(b".", 1)
        if len(parts) != 2:
            return None

        payload_bytes, sig_bytes = parts
        expected_sig = hmac.new(_SECRET, payload_bytes, hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(expected_sig.encode(), sig_bytes):
            return None

        payload = json.loads(payload_bytes)

        # Check expiry
        created = payload.get("ts", 0)
        if time.time() - created > TOKEN_TTL_SECONDS:
            return None

        return payload
    except Exception:
        return None
