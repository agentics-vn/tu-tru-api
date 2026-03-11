"""
thap_than.py — Phase 4: Thập Thần (Ten Gods / 十神).

Maps each Thiên Can's relationship to the Day Master.

Source of truth: docs/algorithm.md §20
"""

from __future__ import annotations

from engine.can_chi import CAN_NAMES, CAN_HANH

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

THAP_THAN_NAMES: dict[str, str] = {
    "ty_kien": "Tỷ Kiên",         # Compare Shoulder
    "kiep_tai": "Kiếp Tài",       # Rob Wealth
    "thuc_than": "Thực Thần",     # Eating God
    "thuong_quan": "Thương Quan",  # Hurting Officer
    "thien_an": "Thiên Ấn",       # Indirect Resource / Owl
    "chinh_an": "Chính Ấn",       # Direct Resource
    "thien_tai": "Thiên Tài",     # Indirect Wealth
    "chinh_tai": "Chính Tài",     # Direct Wealth
    "that_sat": "Thất Sát",       # Seven Killing
    "chinh_quan": "Chính Quan",   # Direct Officer
}


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
    category = "favorable" if key in favorable else "unfavorable"

    return {
        "key": key,
        "name": THAP_THAN_NAMES[key],
        "category": category,
    }


def analyze_thap_than(tu_tru: dict) -> dict:
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

    year_god = get_thap_than(dm_can, tu_tru["year"]["can_idx"])
    month_god = get_thap_than(dm_can, tu_tru["month"]["can_idx"])
    hour_god = get_thap_than(dm_can, tu_tru["hour"]["can_idx"])

    # Count occurrences of each Ten God
    gods = [year_god["key"], month_god["key"], hour_god["key"]]
    god_counts: dict[str, int] = {}
    for g in gods:
        god_counts[g] = god_counts.get(g, 0) + 1

    # Find dominant god
    dominant_key = max(god_counts, key=god_counts.get)

    return {
        "year_god": year_god,
        "month_god": month_god,
        "hour_god": hour_god,
        "god_counts": god_counts,
        "dominant_god": {
            "key": dominant_key,
            "name": THAP_THAN_NAMES[dominant_key],
        },
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
