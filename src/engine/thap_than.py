"""
thap_than.py — Phase 4: Thập Thần (Ten Gods / 十神).

Maps each Thiên Can's relationship to the Day Master.

Source of truth: docs/algorithm.md §20
"""

from __future__ import annotations

from engine.can_chi import CAN_HANH, CAN_NAMES
from engine.hoa_hop import detect_stem_transformations, effective_stem_hanh
from engine.tang_can import get_tang_can, get_tang_can_display

# ─────────────────────────────────────────────────────────────────────────────
# Polarity: Dương (yang) = even index, Âm (yin) = odd index
# Giáp(0)=Dương, Ất(1)=Âm, Bính(2)=Dương, Đinh(3)=Âm, ...
# ─────────────────────────────────────────────────────────────────────────────

def _is_duong(can_idx: int) -> bool:
    """True if Thiên Can is Yang (Dương): Giáp, Bính, Mậu, Canh, Nhâm."""
    return can_idx % 2 == 0


def _same_polarity(a: int, b: int) -> bool:
    """True if both Cans have the same polarity (both Dương or both Âm)."""
    return (a % 2) == (b % 2)


# ─────────────────────────────────────────────────────────────────────────────
# Ngũ Hành relationship functions
# ─────────────────────────────────────────────────────────────────────────────

SINH_MAP: dict[str, str] = {
    "Kim": "Thủy", "Mộc": "Hỏa", "Thủy": "Mộc",
    "Hỏa": "Thổ", "Thổ": "Kim",
}

KHAC_MAP: dict[str, str] = {
    "Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy",
    "Thủy": "Hỏa", "Hỏa": "Kim",
}

# ─────────────────────────────────────────────────────────────────────────────
# Ten God names
# ─────────────────────────────────────────────────────────────────────────────

GOD_GROUPS: dict[str, list[str]] = {
    "ty_kiep": ["ty_kien", "kiep_tai"],
    "thuc_thuong": ["thuc_than", "thuong_quan"],
    "tai_tinh": ["chinh_tai", "thien_tai"],
    "quan_sat": ["chinh_quan", "that_sat"],
    "an_tinh": ["chinh_an", "thien_an"],
}

GOD_GROUP_LABELS: dict[str, str] = {
    "ty_kiep": "Tỷ Kiếp",
    "thuc_thuong": "Thực Thương",
    "tai_tinh": "Tài Tinh",
    "quan_sat": "Quan Sát",
    "an_tinh": "Ấn Tinh",
}

THAP_THAN_NAMES: dict[str, str] = {
    "ty_kien": "Tỷ Kiên",
    "kiep_tai": "Kiếp Tài",
    "thuc_than": "Thực Thần",
    "thuong_quan": "Thương Quan",
    "thien_an": "Thiên Ấn",
    "chinh_an": "Chính Ấn",
    "thien_tai": "Thiên Tài",
    "chinh_tai": "Chính Tài",
    "that_sat": "Thất Sát",
    "chinh_quan": "Chính Quan",
}

THAP_THAN_SHORT_LABELS: dict[str, str] = {
    "ty_kien": "Tỷ",
    "kiep_tai": "Kiếp",
    "thuc_than": "Thực",
    "thuong_quan": "Thương",
    "thien_an": "T.Ấn",
    "chinh_an": "Ấn",
    "thien_tai": "T.Tài",
    "chinh_tai": "Tài",
    "that_sat": "Sát",
    "chinh_quan": "Quan",
}


def short_thap_than_label(god_key: str) -> str:
    return THAP_THAN_SHORT_LABELS.get(god_key, THAP_THAN_NAMES.get(god_key, god_key))


def analyze_pho_tinh(tu_tru: dict) -> dict[str, list[dict]]:
    """
    Thập Thần for each hidden stem (Phó tinh) per pillar.

    Returns dict pillar_key -> list of {can_name, hanh, role, key, name, short_label}.
    """
    dm_can = tu_tru["day"]["can_idx"]
    result: dict[str, list[dict]] = {}
    for pillar_key in ("year", "month", "day", "hour"):
        items: list[dict] = []
        for hidden in get_tang_can_display(tu_tru[pillar_key]["chi_idx"]):
            god = get_thap_than(dm_can, hidden["can_idx"])
            items.append({
                "can_idx": hidden["can_idx"],
                "can_name": hidden["can_name"],
                "hanh": hidden["hanh"],
                "role": hidden["role"],
                "weight": hidden["weight"],
                "key": god["key"],
                "name": god["name"],
                "short_label": short_thap_than_label(god["key"]),
            })
        result[pillar_key] = items
    return result


def analyze_tang_can_display(tu_tru: dict) -> dict[str, list[dict]]:
    """Tàng can labels per pillar for lá số grid."""
    out: dict[str, list[dict]] = {}
    for pillar_key in ("year", "month", "day", "hour"):
        out[pillar_key] = [
            {
                "can_name": h["can_name"],
                "hanh": h["hanh"],
                "role": h["role"],
            }
            for h in get_tang_can_display(tu_tru[pillar_key]["chi_idx"])
        ]
    return out


def get_thap_than(day_master_can: int, target_can: int) -> dict:
    """
    Derive the Ten God relationship from Day Master to another Can.

    Rules:
    Same element + same polarity  → Tỷ Kiên (Compare Shoulder)
    Same element + diff polarity  → Kiếp Tài (Rob Wealth)
    DM generates + same polarity  → Thực Thần (Eating God)
    DM generates + diff polarity  → Thương Quan (Hurting Officer)
    Generates DM + same polarity  → Thiên Ấn (Indirect Resource)
    Generates DM + diff polarity  → Chính Ấn (Direct Resource)
    DM destroys + same polarity   → Thiên Tài (Indirect Wealth)
    DM destroys + diff polarity   → Chính Tài (Direct Wealth)
    Destroys DM + same polarity   → Thất Sát (Seven Killing)
    Destroys DM + diff polarity   → Chính Quan (Direct Officer)

    Args:
        day_master_can: Can index of Day Master (0-9)
        target_can: Can index of the other stem (0-9)

    Returns:
        dict with keys: key, name, category
    """
    dm_hanh = CAN_HANH[day_master_can]
    target_hanh = CAN_HANH[target_can]
    same_pol = _same_polarity(day_master_can, target_can)

    # Same element
    if dm_hanh == target_hanh:
        if same_pol:
            key = "ty_kien"
        else:
            key = "kiep_tai"

    # DM generates target
    elif SINH_MAP[dm_hanh] == target_hanh:
        if same_pol:
            key = "thuc_than"
        else:
            key = "thuong_quan"

    # Target generates DM
    elif SINH_MAP[target_hanh] == dm_hanh:
        if same_pol:
            key = "thien_an"
        else:
            key = "chinh_an"

    # DM destroys (controls) target
    elif KHAC_MAP[dm_hanh] == target_hanh:
        if same_pol:
            key = "thien_tai"
        else:
            key = "chinh_tai"

    # Target destroys (controls) DM
    elif KHAC_MAP[target_hanh] == dm_hanh:
        if same_pol:
            key = "that_sat"
        else:
            key = "chinh_quan"

    else:
        # Should not happen with correct Ngũ Hành logic
        key = "ty_kien"  # fallback

    # Categorize as favorable/unfavorable for general reference
    favorable = {"ty_kien", "chinh_an", "thien_an", "thuc_than", "chinh_tai"}
    category = "thuận lợi" if key in favorable else "bất lợi"

    return {
        "key": key,
        "name": THAP_THAN_NAMES[key],
        "category": category,
    }


def _god_key_from_can(dm_can: int, target_can: int) -> str:
    return get_thap_than(dm_can, target_can)["key"]


def _god_key_transformed(
    dm_can: int,
    original_can: int,
    transform_hanh: str,
) -> str:
    """Ten God for a stem after 合化 — 化神 element, polarity from original stem."""
    dm_hanh = CAN_HANH[dm_can]
    same_pol = (dm_can % 2) == (original_can % 2)
    if transform_hanh == dm_hanh:
        return "ty_kien" if same_pol else "kiep_tai"
    if SINH_MAP[transform_hanh] == dm_hanh:
        return "chinh_an" if not same_pol else "thien_an"
    if SINH_MAP[dm_hanh] == transform_hanh:
        return "thuc_than" if same_pol else "thuong_quan"
    if KHAC_MAP[dm_hanh] == transform_hanh:
        return "chinh_tai" if not same_pol else "thien_tai"
    if KHAC_MAP[transform_hanh] == dm_hanh:
        return "chinh_quan" if not same_pol else "that_sat"
    return "ty_kien"


def analyze_god_groups(
    tu_tru: dict,
    transforms: list[dict] | None = None,
) -> dict:
    """
    Weighted Ten God group energy (surface stems + hidden stems).
    Surface stems after 合化 use transformed element vs DM.
    """
    dm_can = tu_tru["day"]["can_idx"]
    if transforms is None:
        transforms = detect_stem_transformations(tu_tru)
    weights: dict[str, float] = {k: 0.0 for k in GOD_GROUPS}

    for pillar_key in ("year", "month", "hour"):
        can_idx = tu_tru[pillar_key]["can_idx"]
        eff_hanh, transformed = effective_stem_hanh(
            pillar_key, can_idx, transforms,
        )
        if transformed:
            god_key = _god_key_transformed(dm_can, can_idx, eff_hanh)
        else:
            god_key = _god_key_from_can(dm_can, can_idx)
        for group, keys in GOD_GROUPS.items():
            if god_key in keys:
                weights[group] += 1.0
                break

    for pillar_key in ("year", "month", "day", "hour"):
        for hidden in get_tang_can(tu_tru[pillar_key]["chi_idx"]):
            god_key = _god_key_from_can(dm_can, hidden["can_idx"])
            w = hidden["weight"]
            for group, keys in GOD_GROUPS.items():
                if god_key in keys:
                    weights[group] += w
                    break

    total = sum(weights.values())
    percent: dict[str, float] = {}
    if total > 0:
        for group, w in weights.items():
            percent[group] = round(w / total * 100, 1)
    else:
        for group in GOD_GROUPS:
            percent[group] = 0.0

    return {
        "weights": {k: round(v, 2) for k, v in weights.items()},
        "percent": percent,
        "labels": GOD_GROUP_LABELS,
    }


def analyze_thap_than(
    tu_tru: dict,
    transforms: list[dict] | None = None,
) -> dict:
    """
    Map all 4 pillars' Cans to their Ten God relationships.

    Args:
        tu_tru: dict from get_tu_tru() with year/month/day/hour pillars

    Returns:
        dict with keys:
            year_god, month_god, hour_god: Ten God dicts
            profile: summary of dominant gods
            dominant_god: the most prominent Ten God (by count)
    """
    dm_can = tu_tru["day"]["can_idx"]
    if transforms is None:
        transforms = detect_stem_transformations(tu_tru)

    def _pillar_god(pillar_key: str) -> dict:
        can_idx = tu_tru[pillar_key]["can_idx"]
        eff_hanh, transformed = effective_stem_hanh(
            pillar_key, can_idx, transforms,
        )
        if transformed:
            key = _god_key_transformed(dm_can, can_idx, eff_hanh)
            return {
                "key": key,
                "name": THAP_THAN_NAMES[key],
                "category": (
                    "thuận lợi"
                    if key in {"ty_kien", "chinh_an", "thien_an", "thuc_than", "chinh_tai"}
                    else "bất lợi"
                ),
            }
        return get_thap_than(dm_can, can_idx)

    year_god = _pillar_god("year")
    month_god = _pillar_god("month")
    hour_god = _pillar_god("hour")

    gods = [year_god["key"], month_god["key"], hour_god["key"]]
    god_counts: dict[str, int] = {}
    for g in gods:
        god_counts[g] = god_counts.get(g, 0) + 1

    # Find dominant god
    dominant_key = max(god_counts, key=god_counts.get)

    god_groups = analyze_god_groups(tu_tru, transforms)

    return {
        "year_god": year_god,
        "month_god": month_god,
        "hour_god": hour_god,
        "god_counts": god_counts,
        "surface_god_counts": god_counts,
        "god_groups": god_groups,
        "dominant_god": {
            "key": dominant_key,
            "name": THAP_THAN_NAMES[dominant_key],
        },
        "dominant_god_group": _dominant_god_group(god_groups),
    }


def _dominant_god_group(god_groups: dict) -> dict:
    group_key = max(god_groups["percent"], key=god_groups["percent"].get)
    return {
        "key": group_key,
        "name": GOD_GROUP_LABELS[group_key],
        "percent": god_groups["percent"][group_key],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Intent ↔ Ten God alignment (for scoring bonus)
# ─────────────────────────────────────────────────────────────────────────────

# Which Ten God on a day is especially favorable for which intent
INTENT_GOD_BONUS: dict[str, list[str]] = {
    "CAU_TAI": ["chinh_tai", "thien_tai"],
    "KHAI_TRUONG": ["chinh_tai", "thuc_than"],
    "KY_HOP_DONG": ["chinh_tai", "chinh_quan"],
    "DAM_CUOI": ["chinh_tai", "chinh_an"],
    "AN_HOI": ["chinh_tai", "chinh_an"],
    "NHAM_CHUC": ["chinh_quan", "chinh_an"],
    "NHAP_HOC_THI_CU": ["chinh_an", "thien_an"],
    "KHAM_BENH": ["chinh_an", "thuc_than"],
    "XUAT_HANH": ["thuc_than", "chinh_tai"],
    "DONG_THO": ["chinh_tai", "thuc_than"],
    "NHAP_TRACH": ["chinh_an", "chinh_tai"],
    "KIEN_TUNG": ["that_sat", "chinh_quan"],
    "TE_TU": ["chinh_an", "thien_an"],
}


def get_day_god_for_intent(day_can_idx: int, dm_can_idx: int, intent: str) -> dict | None:
    """
    Check if the day's Ten God aligns favorably with the intent.

    Args:
        day_can_idx: the day's Thiên Can index
        dm_can_idx: the user's Day Master Can index
        intent: intent key string

    Returns:
        The Ten God dict if alignment is favorable, else None
    """
    god = get_thap_than(dm_can_idx, day_can_idx)
    favorable_gods = INTENT_GOD_BONUS.get(intent, [])

    if god["key"] in favorable_gods:
        return god
    return None
