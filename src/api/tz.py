"""
Timezone helpers (T4-04).

Resolves ``date.today()`` to the caller's local date using an optional
IANA timezone string (e.g. ``Asia/Ho_Chi_Minh``, ``America/Los_Angeles``).
Defaults to ``Asia/Ho_Chi_Minh`` when no timezone is provided.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TZ = "Asia/Ho_Chi_Minh"


def today_in_tz(tz: str | None = None) -> date:
    """Return today's date in the given IANA timezone.

    Raises ``ValueError`` if the timezone string is not recognized.
    """
    tz_name = tz or DEFAULT_TZ
    try:
        zone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise ValueError(f"Timezone không hợp lệ: {tz_name}")
    return datetime.now(tz=zone).date()
