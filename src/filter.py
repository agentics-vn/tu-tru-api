"""
filter.py — Layer 2: Personal chart + intent-specific date filter.

Ported from filter.js.
Source of truth: docs/algorithm.md §9.
"""

from __future__ import annotations

from engine.can_chi import is_can_khac, is_xung

# ─────────────────────────────────────────────────────────────────────────────
# Tháng Cô Hồn blocked intents
# ─────────────────────────────────────────────────────────────────────────────

# Only intents with _special_rules.avoid_lunar_month_7 in intent-rules.json.
# Algorithm.md §5.4 specifies CUOI_HOI (→ DAM_CUOI via alias).
# Intent-rules.json extends to DONG_THO and NHAP_TRACH.
COHON_BLOCKED_INTENTS: frozenset[str] = frozenset({
    "DAM_CUOI", "DONG_THO", "NHAP_TRACH",
})

# ─────────────────────────────────────────────────────────────────────────────
# Intent labels (Vietnamese)
# ─────────────────────────────────────────────────────────────────────────────

INTENT_LABELS: dict[str, str] = {
    "KHAI_TRUONG": "Khai trương",
    "KY_HOP_DONG": "Ký kết hợp đồng",
    "AN_HOI": "Lễ ăn hỏi",
    "DAM_CUOI": "Đám cưới",
    "DONG_THO": "Động thổ",
    "NHAP_TRACH": "Nhập trạch",
    "LAM_NHA": "Làm nhà",
    "AN_TANG": "An táng",
    "CAI_TANG": "Cải táng",
    "XUAT_HANH": "Xuất hành",
    "CAU_TAI": "Cầu tài lộc",
    "TE_TU": "Tế tự",
    "KHAM_BENH": "Khám bệnh",
    "PHAU_THUAT": "Phẫu thuật",
    "NHAP_HOC_THI_CU": "Nhập học / Thi cử",
    "NHAM_CHUC": "Nhậm chức",
    "MUA_NHA_DAT": "Mua nhà đất",
    "DAO_GIENG": "Đào giếng",
    "TRONG_CAY": "Trồng cây",
    "CAU_TU": "Cầu tự",
    "XAY_BEP": "Xây bếp",
    "LAM_GIUONG": "Làm giường",
    "KIEN_TUNG": "Kiện tụng",
    "DI_CHUYEN_NGOAI": "Xuất ngoại",
    "GIAI_HAN": "Giải hạn",
    "MAC_DINH": "Sự kiện chung",
}


def _intent_label(intent: str) -> str:
    return INTENT_LABELS.get(intent, intent)


# ─────────────────────────────────────────────────────────────────────────────
# Main filter function
# ─────────────────────────────────────────────────────────────────────────────

def apply_layer2_filter(day_info: dict, user_chart: dict, intent: str) -> dict:
    """
    Apply Layer 2 personal + intent filter.

    Args:
        day_info: from get_day_info()
        user_chart: from get_user_chart()
        intent: intent key string

    Returns:
        dict with keys: pass (bool), severity (0|2|3), reasons (list[str])
    """
    reasons: list[str] = []
    max_severity = 0

    # SPECIAL RULE 3: Tháng Cô Hồn
    if day_info["is_cohon"] and intent in COHON_BLOCKED_INTENTS:
        return {
            "pass": False,
            "severity": 3,
            "reasons": [
                f"Tháng Cô Hồn (tháng 7 âm lịch) — không thích hợp cho {_intent_label(intent)}"
            ],
        }

    # R1: Địa Chi Tương Xung (severity 3)
    if is_xung(day_info["day_chi_idx"], user_chart["year_chi_idx"]):
        return {
            "pass": False,
            "severity": 3,
            "reasons": [
                f"Địa Chi ngày {day_info['day_chi_name']} xung với tuổi {user_chart['year_chi_name']}"
            ],
        }

    # R2: Thiên Can Tương Khắc (severity 2)
    if is_can_khac(day_info["day_can_idx"], user_chart["year_can_idx"]):
        max_severity = max(max_severity, 2)
        reasons.append(
            f"Thiên Can ngày {day_info['day_can_name']} khắc Thiên Can tuổi {user_chart['year_can_name']}"
        )

    # R3: Ngày có hành Kỵ Thần (severity 2)
    # Use chart-aware ky_than_v2 (Dụng Thần system) when available,
    # otherwise fall back to simplified ky_than (Nạp Âm system)
    effective_ky_than = user_chart.get("ky_than_v2") or user_chart["ky_than"]
    if day_info["day_nap_am_hanh"] == effective_ky_than:
        max_severity = max(max_severity, 2)
        if user_chart.get("ky_than_v2"):
            reasons.append(
                f"Nạp Âm ngày ({day_info['day_nap_am_hanh']}) là Kỵ Thần "
                f"của Nhật Chủ {user_chart['nhat_chu']['can_name']} ({user_chart['chart_strength']})"
            )
        else:
            reasons.append(
                f"Nạp Âm ngày ({day_info['day_nap_am_hanh']}) là Kỵ Thần của mệnh {user_chart['menh_name']}"
            )

    return {
        "pass": True,
        "severity": max_severity,
        "reasons": reasons,
    }
