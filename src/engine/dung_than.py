"""
dung_than.py — Phase 3b: Dụng Thần (Useful God / 用神) identification.

Replaces the simplistic Dương Thần / Kỵ Thần with chart-aware element analysis.

Uses the Cường Nhược (Strong/Weak) method (強弱法):
- Weak Day Master → support it (Ấn Tinh / Tỷ Kiên)
- Strong Day Master → drain/control it (Thực Thương / Tài Tinh / Quan Sát)

Source of truth: docs/algorithm.md §19

Luật ``2026-10.1`` (docs/algorithm.md §23, ``engine.dung_than_v2``) chỉ chạy khi người gọi
truyền ``rule="2026-10.1"``; vắng hoặc ``"v1"`` thì giữ nguyên luật cũ.
"""

from __future__ import annotations

from engine import dung_than_v2
from engine.cuong_nhuoc import analyze_chart_strength

RULE_V1 = "v1"
RULE_V2 = dung_than_v2.RULE_VERSION      # "2026-10.1"
RULES = (RULE_V1, RULE_V2)

# ─────────────────────────────────────────────────────────────────────────────
# Ngũ Hành relationship maps
# ─────────────────────────────────────────────────────────────────────────────

# Element that generates the target (Ấn Tinh direction)
SINH_BY: dict[str, str] = {
    "Kim": "Thổ", "Mộc": "Thủy", "Thủy": "Kim",
    "Hỏa": "Mộc", "Thổ": "Hỏa",
}

# Element that the target generates (Thực Thương direction)
SINH_TARGET: dict[str, str] = {
    "Kim": "Thủy", "Mộc": "Hỏa", "Thủy": "Mộc",
    "Hỏa": "Thổ", "Thổ": "Kim",
}

# Element that the target controls (Tài Tinh direction)
KHAC_TARGET: dict[str, str] = {
    "Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy",
    "Thủy": "Hỏa", "Hỏa": "Kim",
}

# Element that controls the target (Quan Sát direction)
KHAC_BY: dict[str, str] = {
    "Kim": "Hỏa", "Mộc": "Kim", "Thủy": "Thổ",
    "Hỏa": "Thủy", "Thổ": "Mộc",
}


def find_dung_than(
    tu_tru: dict,
    analysis: dict | None = None,
    rule: str = RULE_V1,
    co_gio: bool = True,
) -> dict:
    """
    Find the Useful God element based on chart balance.

    ``rule``: ``"v1"`` (mặc định, luật bên dưới, đầu ra không đổi) hoặc ``"2026-10.1"``
    (trả các trường đặc tả 8.1 của ``dung_than_v2.tinh`` cộng ``strength`` và ``analysis``
    như v1 để người gọi cũ không gãy). ``co_gio=False`` chỉ có nghĩa ở ``2026-10.1``.

    Core logic (Cường Nhược pháp):
    - Weak Day Master → Dụng Thần = element that SUPPORTS it
      Primary: Ấn Tinh (parent element), Secondary: Tỷ Kiên (same element)
    - Strong Day Master → Dụng Thần = element that DRAINS it
      Primary: Thực Thương (child element), Secondary: Tài Tinh (wealth element)
    - Balanced → use the element most needed to maintain balance

    Also determines:
    - Hỷ Thần: secondary helpful element (supports Dụng Thần)
    - Kỵ Thần: most harmful element (opposes Dụng Thần)
    - Cừu Thần: element that generates Kỵ Thần

    Args:
        tu_tru: dict from get_tu_tru()

    Returns:
        dict with keys:
            dung_than: str (element name)
            hi_than: str
            ky_than: str
            cuu_than: str
            strength: str ("vượng" | "nhược" | "cân bằng")
            analysis: dict (full strength analysis)
    """
    if rule not in RULES:
        raise ValueError(f"dung_than_rule không hợp lệ: {rule!r} (nhận {', '.join(RULES)})")
    if rule == RULE_V2:
        return _find_dung_than_v2(tu_tru, analysis, co_gio)
    if not co_gio:
        raise ValueError("dung_than_rule 'v1' không có nhánh thiếu giờ (co_gio=False)")

    analysis = analysis if analysis is not None else analyze_chart_strength(tu_tru)
    strength = analysis["strength"]
    dm_hanh = analysis["day_master_hanh"]
    element_counts = analysis["element_counts"]

    if strength == "nhược":
        # Weak Day Master needs support
        # Primary Dụng Thần: Ấn Tinh (parent element that generates DM)
        # Secondary: Tỷ Kiên (same element)
        dung_than = SINH_BY[dm_hanh]  # Parent (e.g. Mộc generates Hỏa)
        hi_than = dm_hanh              # Same element = Tỷ Kiên support

        # Kỵ Thần: element that controls DM (weakens further)
        ky_than = KHAC_BY[dm_hanh]     # e.g. Thủy controls Hỏa
        # Cừu Thần: element that generates Kỵ Thần
        cuu_than = SINH_BY[ky_than]

    elif strength == "vượng":
        # Strong Day Master needs draining
        # Primary Dụng Thần: Thực Thương (element DM generates = drain energy)
        # Or Quan Sát (element that controls DM)
        # Choose whichever is weaker in the chart (more needed)
        child = SINH_TARGET[dm_hanh]   # DM generates this
        controller = KHAC_BY[dm_hanh]  # Controls DM

        # Pick whichever has less presence (more needed)
        if element_counts.get(child, 0) <= element_counts.get(controller, 0):
            dung_than = child
        else:
            dung_than = controller

        # Hỷ Thần: secondary drain element
        hi_than = KHAC_TARGET[dm_hanh]  # Tài Tinh (DM controls it = spending energy)

        # Kỵ Thần: element that generates DM (makes it even stronger)
        ky_than = SINH_BY[dm_hanh]      # Ấn Tinh becomes harmful
        cuu_than = SINH_BY[ky_than]

    else:
        # Balanced — maintain equilibrium
        # Dụng Thần: element that DM generates (gentle drain)
        dung_than = SINH_TARGET[dm_hanh]
        hi_than = dm_hanh  # Same element for stability

        # Least desirable: whatever would tip the balance
        # The most abundant non-DM element is Kỵ Thần
        non_dm = {k: v for k, v in element_counts.items() if k != dm_hanh}
        ky_than = max(non_dm, key=non_dm.get) if non_dm else KHAC_BY[dm_hanh]
        cuu_than = SINH_BY[ky_than]

    return {
        "dung_than": dung_than,
        "hi_than": hi_than,
        "ky_than": ky_than,
        "cuu_than": cuu_than,
        "strength": strength,
        "analysis": analysis,
    }


def _find_dung_than_v2(tu_tru: dict, analysis: dict | None, co_gio: bool) -> dict:
    """Luật 2026-10.1. ``strength`` = ``cuong_nhuoc`` của chính luật, để một đầu ra không mang
    hai nhãn (khớp nhãn v1 ở 6.785/6.786 lá số mẫu; lệch khi r đúng ngưỡng, algorithm.md §23.2).
    ``analysis`` là phân tích cường nhược v1 của tứ trụ (không có trụ giờ thì None)."""
    kq = dung_than_v2.tinh(tu_tru, co_gio=co_gio)
    if analysis is None and isinstance(tu_tru.get("hour"), dict):
        analysis = analyze_chart_strength(tu_tru)
    return {**kq, "strength": kq["cuong_nhuoc"], "analysis": analysis}
