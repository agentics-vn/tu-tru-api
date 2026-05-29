"""Load and validate intent keys from docs/seed/intent-rules.json."""

from __future__ import annotations

import json
from pathlib import Path

_INTENT_RULES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "seed" / "intent-rules.json"
)
with open(_INTENT_RULES_PATH, encoding="utf-8") as _f:
    INTENT_RULES: dict = json.load(_f)

VALID_INTENT_KEYS: frozenset[str] = frozenset(
    k for k in INTENT_RULES if not k.startswith("_")
)

# POST /v1/chon-ngay accepts CUOI_HOI → DAM_CUOI
INTENT_QUERY_ALIASES: dict[str, str] = {
    "CUOI_HOI": "DAM_CUOI",
}

_REQUIRED_FIELDS = {"preferred_truc", "forbidden_truc", "bonus_sao", "forbidden_sao"}
_VALID_TRUC = set(range(12))


def _validate_intent_rules_schema() -> None:
    """Fail fast at import if seed data is malformed (T1-08)."""
    for key, rule in INTENT_RULES.items():
        if key.startswith("_"):
            continue
        missing = _REQUIRED_FIELDS - set(rule.keys())
        if missing:
            raise RuntimeError(
                f"intent-rules.json: intent '{key}' missing fields: {missing}"
            )
        for field in ("preferred_truc", "forbidden_truc"):
            if not isinstance(rule[field], list):
                raise RuntimeError(
                    f"intent-rules.json: intent '{key}'.{field} must be a list"
                )
            for idx in rule[field]:
                if not isinstance(idx, int) or idx not in _VALID_TRUC:
                    raise RuntimeError(
                        f"intent-rules.json: intent '{key}'.{field} has invalid index {idx}"
                    )
        for field in ("bonus_sao", "forbidden_sao"):
            if not isinstance(rule[field], list):
                raise RuntimeError(
                    f"intent-rules.json: intent '{key}'.{field} must be a list"
                )
            for sao in rule[field]:
                if not isinstance(sao, str) or not sao:
                    raise RuntimeError(
                        f"intent-rules.json: intent '{key}'.{field} has invalid entry '{sao}'"
                    )


_validate_intent_rules_schema()


def resolve_intent_key(intent: str) -> str:
    """Map API intent to intent-rules.json key; raise ValueError if unknown."""
    key = INTENT_QUERY_ALIASES.get(intent, intent)
    if key not in VALID_INTENT_KEYS:
        raise ValueError(
            f"intent không hợp lệ: {intent}. "
            f"Giá trị hợp lệ: {', '.join(sorted(VALID_INTENT_KEYS))}"
        )
    return key


def get_intent_rule(intent: str) -> dict:
    """Resolve intent and return rule dict from seed."""
    key = resolve_intent_key(intent)
    return INTENT_RULES.get(
        key,
        INTENT_RULES["MAC_DINH"],
    )
