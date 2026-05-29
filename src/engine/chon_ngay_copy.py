"""
Prose helpers for chon-ngay ranked row copy (Direction C).
"""

from __future__ import annotations


def build_chon_ngay_reason_vi(
    *,
    grade: str,
    truc_name: str,
    can_chi_day: str,
    intent_label_vi: str,
) -> str:
    """Fallback when summary_vi is empty — never join reasons_vi[]."""
    grade_text = {
        "A": "Ngày rất thuận",
        "B": "Ngày khá thuận",
        "C": "Ngày ở mức trung bình",
        "D": "Ngày không thuận lắm",
    }.get(grade, "Ngày cần cân nhắc")
    return (
        f"{grade_text} cho {intent_label_vi.lower()}: Trực {truc_name}, "
        f"Can Chi {can_chi_day}. Xem chi tiết từng yếu tố trong phần luận giải."
    )
