"""
dung_than.py — Phase 3b: Dụng Thần (Useful God / 用神) identification.

Replaces the simplistic Dương Thần / Kỵ Thần with chart-aware element analysis.

Uses the Cường Nhược (Strong/Weak) method (強弱法):
- Weak Day Master → support it (Ấn Tinh / Tỷ Kiên)
- Strong Day Master → drain/control it (Thực Thương / Tài Tinh / Quan Sát)

Source of truth: docs/algorithm.md §19
"""

from __future__ import annotations

from engine.cuong_nhuoc import analyze_chart_strength

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

NGU_HANH: tuple[str, ...] = ("Mộc", "Hỏa", "Thổ", "Kim", "Thủy")

VAI_DUNG = "Dụng"
VAI_HI = "Hỉ"
VAI_KY = "Kỵ"
VAI_CUU = "Cừu"


def assign_vai_5_hanh(dm_hanh: str, dung_than: str) -> dict[str, str]:
    """
    Gán TRỌN 5 hành vào đúng một vai Dụng/Hỉ/Kỵ/Cừu — không để hành nào lửng lơ.

    Nguồn: BT285 Rule 0 BƯỚC 4 ("PHÂN VAI TRỌN 5 HÀNH"). Đây là hợp đồng dữ
    liệu mà prompt sinh bài dựa vào: nếu một hành không có vai, mỗi mục sẽ tự
    diễn giải lại và sinh mâu thuẫn giữa các mục.

    Nhánh được chọn theo CHỖ ĐỨNG CỦA DỤNG THẦN, không theo nhãn cường nhược:

    * Dụng nằm ở nhóm ức chế thân (Thực Thương / Tài / Quan Sát) — ca thân
      vượng, ca cân bằng, và cả ca tòng:
        Ấn = Kỵ, Tỷ Kiếp = Cừu (nuôi thân đã quá vượng, hoặc phá tòng).
        Hai hành ức chế còn lại phân theo QUY ƯỚC QUAN SÁT của Rule 0:
          Dụng = Thực Thương → Tài = Hỉ, Quan Sát = Kỵ (Thương Quan kiến Quan)
          Dụng = Tài         → Thực Thương = Hỉ, Quan Sát = Hỉ (dòng sinh thuận)
          Dụng = Quan Sát    → Tài = Hỉ, Thực Thương = Kỵ (khắc gãy dòng chảy)

    * Dụng nằm ở nhóm phù thân (Ấn / Tỷ Kiếp) — ca thân nhược:
        Hành phù thân còn lại = Hỉ. Cả ba hành tiết-khắc-hao thân đều bất lợi:
        hành khắc Dụng và hành khắc Nhật Chủ = Kỵ, phần còn lại = Cừu.

    Args:
        dm_hanh: hành của Nhật Chủ
        dung_than: hành đã chốt ở Bước 2

    Returns:
        dict 5 khóa (mỗi hành → một vai). Bất biến: đủ 5 hành, đúng một vai
        Dụng, và không hành nào thiếu vai.
    """
    an = SINH_BY[dm_hanh]            # Ấn — sinh Nhật Chủ
    ty_kiep = dm_hanh                # Tỷ Kiếp — cùng hành Nhật Chủ
    thuc_thuong = SINH_TARGET[dm_hanh]  # Thực Thương — Nhật Chủ sinh ra
    tai = KHAC_TARGET[dm_hanh]       # Tài — Nhật Chủ khắc
    quan_sat = KHAC_BY[dm_hanh]      # Quan Sát — khắc Nhật Chủ

    vai: dict[str, str] = {}

    if dung_than in (thuc_thuong, tai, quan_sat):
        vai[an] = VAI_KY
        vai[ty_kiep] = VAI_CUU
        if dung_than == thuc_thuong:
            vai[tai] = VAI_HI
            vai[quan_sat] = VAI_KY
        elif dung_than == tai:
            vai[thuc_thuong] = VAI_HI
            vai[quan_sat] = VAI_HI
        else:  # dung_than == quan_sat
            vai[tai] = VAI_HI
            vai[thuc_thuong] = VAI_KY
    else:
        # Dụng thuộc nhóm phù thân → thân nhược
        vai[an if dung_than == ty_kiep else ty_kiep] = VAI_HI
        attackers = {KHAC_BY[dung_than], KHAC_BY[dm_hanh]}
        for hanh in (thuc_thuong, tai, quan_sat):
            vai[hanh] = VAI_KY if hanh in attackers else VAI_CUU

    # Dụng thần ghi sau cùng để không bị nhánh nào ghi đè
    vai[dung_than] = VAI_DUNG

    missing = [h for h in NGU_HANH if h not in vai]
    if missing:  # pragma: no cover — bất biến, chỉ nổ khi map ngũ hành hỏng
        raise ValueError(
            f"vai_5_hanh thiếu hành {missing} (dm={dm_hanh}, dụng={dung_than})"
        )
    return {h: vai[h] for h in NGU_HANH}


def _dai_dien(vai_5_hanh: dict[str, str], vai: str, uu_tien: str | None = None) -> str | None:
    """Chọn một hành đại diện cho vai, ưu tiên hành gọi ý nếu nó mang đúng vai đó."""
    ung_vien = [h for h in NGU_HANH if vai_5_hanh[h] == vai]
    if not ung_vien:
        return None
    if uu_tien in ung_vien:
        return uu_tien
    return ung_vien[0]


def find_dung_than(tu_tru: dict, analysis: dict | None = None) -> dict:
    """
    Find the Useful God element based on chart balance.

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

    # hi_than / ky_than / cuu_than giữ NGUYÊN công thức cũ — chúng là đầu vào đã
    # hiệu chỉnh của bộ chấm điểm ngày tốt (scoring.py, filter.py). Cố ý không
    # suy lại từ vai_5_hanh: làm vậy sẽ đổi điểm ngày tốt ở cả 25/25 tổ hợp
    # Nhật Chủ × thân × Dụng. vai_5_hanh là hợp đồng riêng cho phần luận giải.
    return {
        "dung_than": dung_than,
        "hi_than": hi_than,
        "ky_than": ky_than,
        "cuu_than": cuu_than,
        "vai_5_hanh": assign_vai_5_hanh(dm_hanh, dung_than),
        "strength": strength,
        "analysis": analysis,
    }
