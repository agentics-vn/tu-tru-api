"""API version stamps for Direction C P2-03."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def get_engine_version() -> str:
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    if pyproject.exists():
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            if line.startswith("version = "):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0.1.1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
