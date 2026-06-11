"""
hoa_hop.py — Thiên Can Ngũ Hợp Hóa (天干五合化气).

Detects stem combinations that transform to a new element when 月令 supports 化神.

Source of truth: docs/algorithm.md §21
"""

from __future__ import annotations

from engine.can_chi import CAN_HANH, CAN_NAMES

# Giáp-Kỷ→Thổ, Ất-Canh→Kim, Bính-Tân→Thủy, Đinh-Nhâm→Mộc, Mậu-Quý→Hỏa
_COMBINE_RESULT: dict[frozenset[int], str] = {
    frozenset({0, 5}): "Thổ",
    frozenset({1, 6}): "Kim",
    frozenset({2, 7}): "Thủy",
    frozenset({3, 8}): "Mộc",
    frozenset({4, 9}): "Hỏa",
}

# Địa Chi → hành bản khí (branch element)
_CHI_ELEMENT: dict[int, str] = {
    0: "Thủy", 1: "Thổ", 2: "Mộc", 3: "Mộc", 4: "Thổ", 5: "Hỏa",
    6: "Hỏa", 7: "Thổ", 8: "Kim", 9: "Kim", 10: "Thổ", 11: "Thủy",
}

# Element that generates target (sinh →)
_SINH_MAP: dict[str, str] = {
    "Kim": "Thủy", "Mộc": "Hỏa", "Thủy": "Mộc",
    "Hỏa": "Thổ", "Thổ": "Kim",
}

_PILLAR_KEYS = ("year", "month", "day", "hour")
_ADJACENT_PAIRS: tuple[tuple[str, str], ...] = (
    ("year", "month"),
    ("month", "day"),
    ("day", "hour"),
)


def _combine_result(can_a: int, can_b: int) -> str | None:
    return _COMBINE_RESULT.get(frozenset({can_a, can_b}))


def month_supports_transform(month_chi_idx: int, transform_element: str) -> bool:
    """
    月令是否支持化神 — month branch element equals or generates transform element.
    """
    branch_el = _CHI_ELEMENT[month_chi_idx]
    if branch_el == transform_element:
        return True
    return _SINH_MAP.get(branch_el) == transform_element


def detect_stem_transformations(tu_tru: dict) -> list[dict]:
    """
    Find successful 合化 among adjacent pillar stems.

    Returns list of dicts:
        pillar_a, pillar_b, can_a, can_b, can_a_name, can_b_name,
        transform_element, success (bool)
    Only successful transforms are returned.
    """
    month_chi_idx = tu_tru["month"]["chi_idx"]
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for pa, pb in _ADJACENT_PAIRS:
        can_a = tu_tru[pa]["can_idx"]
        can_b = tu_tru[pb]["can_idx"]
        if can_a == can_b:
            continue
        result_el = _combine_result(can_a, can_b)
        if not result_el:
            continue
        key = tuple(sorted((pa, pb)))
        if key in seen:
            continue
        if not month_supports_transform(month_chi_idx, result_el):
            continue
        seen.add(key)
        out.append({
            "pillar_a": pa,
            "pillar_b": pb,
            "can_a": can_a,
            "can_b": can_b,
            "can_a_name": CAN_NAMES[can_a],
            "can_b_name": CAN_NAMES[can_b],
            "original_a_hanh": CAN_HANH[can_a],
            "original_b_hanh": CAN_HANH[can_b],
            "transform_element": result_el,
            "success": True,
            "label_vi": (
                f"{CAN_NAMES[can_a]}–{CAN_NAMES[can_b]} hóa {result_el}"
            ),
        })
    return out


def transformed_pillar_stems(transforms: list[dict]) -> set[str]:
    """Pillar keys whose surface stem is neutralized by 合化."""
    stems: set[str] = set()
    for t in transforms:
        stems.add(t["pillar_a"])
        stems.add(t["pillar_b"])
    return stems


def _pillar_transform_element(
    pillar: str,
    transforms: list[dict],
) -> str | None:
    for t in transforms:
        if t["pillar_a"] == pillar:
            return t["transform_element"]
        if t["pillar_b"] == pillar:
            return t["transform_element"]
    return None


def apply_transformations_to_elements(
    base_counts: dict[str, float],
    tu_tru: dict,
    transforms: list[dict],
) -> dict[str, float]:
    """
    Adjust element weights: each transformed surface stem loses original element,
    gains transform_element (1.0 per stem position).
    """
    if not transforms:
        return dict(base_counts)

    counts = dict(base_counts)
    for pillar in _PILLAR_KEYS:
        transform_el = _pillar_transform_element(pillar, transforms)
        if not transform_el:
            continue
        orig = CAN_HANH[tu_tru[pillar]["can_idx"]]
        counts[orig] = max(0.0, counts.get(orig, 0.0) - 1.0)
        counts[transform_el] = counts.get(transform_el, 0.0) + 1.0

    return counts


def effective_stem_hanh(
    pillar: str,
    can_idx: int,
    transforms: list[dict],
) -> tuple[str, bool]:
    """
    Return (effective_element, is_transformed) for a pillar surface stem.
    """
    for t in transforms:
        if t["pillar_a"] == pillar and t["can_a"] == can_idx:
            return t["transform_element"], True
        if t["pillar_b"] == pillar and t["can_b"] == can_idx:
            return t["transform_element"], True
    return CAN_HANH[can_idx], False


def build_stem_transformations_payload(
    tu_tru: dict,
    transforms: list[dict] | None = None,
) -> list[dict]:
    """API-facing list of successful 合化."""
    month_chi = tu_tru["month"]["chi_name"]
    if transforms is None:
        transforms = detect_stem_transformations(tu_tru)
    payload = []
    for t in transforms:
        payload.append({
            "pillars": [t["pillar_a"], t["pillar_b"]],
            "stems": [t["can_a_name"], t["can_b_name"]],
            "transform_element": t["transform_element"],
            "month_chi": month_chi,
            "label_vi": t["label_vi"],
        })
    return payload
