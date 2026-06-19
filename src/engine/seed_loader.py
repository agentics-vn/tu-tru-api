"""Load JSON seed files from docs/seed/."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


def seed_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "docs" / "seed"


@lru_cache(maxsize=32)
def load_seed_json(filename: str) -> dict[str, Any]:
    path = seed_root() / filename
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{filename} must be a JSON object")
    return data
