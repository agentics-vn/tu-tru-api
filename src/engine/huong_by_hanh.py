"""
huong_by_hanh.py — Bảng hướng theo ngũ hành (Dụng Thần).

Shared by phong-thuy và lưu niên (quy_nhan) để tránh coupling chéo module.
"""

from __future__ import annotations

HUONG_BY_HANH: dict[str, list[dict]] = {
    "Kim": [
        {"direction": "Tây", "element": "Kim", "reason": "Chính Tây thuộc Kim — hành Dụng Thần."},
        {"direction": "Tây Bắc", "element": "Kim", "reason": "Tây Bắc thuộc Kim — hỗ trợ sự nghiệp."},
        {"direction": "Đông Bắc", "element": "Thổ", "reason": "Thổ sinh Kim — gián tiếp hỗ trợ."},
    ],
    "Mộc": [
        {"direction": "Đông", "element": "Mộc", "reason": "Chính Đông thuộc Mộc — hành Dụng Thần."},
        {"direction": "Đông Nam", "element": "Mộc", "reason": "Đông Nam thuộc Mộc — hỗ trợ sự nghiệp."},
        {"direction": "Bắc", "element": "Thủy", "reason": "Thủy sinh Mộc — gián tiếp hỗ trợ."},
    ],
    "Thủy": [
        {"direction": "Bắc", "element": "Thủy", "reason": "Chính Bắc thuộc Thủy — hành Dụng Thần."},
        {"direction": "Tây", "element": "Kim", "reason": "Kim sinh Thủy — gián tiếp hỗ trợ."},
        {"direction": "Tây Bắc", "element": "Kim", "reason": "Tây Bắc thuộc Kim — sinh Thủy."},
    ],
    "Hỏa": [
        {"direction": "Nam", "element": "Hỏa", "reason": "Chính Nam thuộc Hỏa — hành Dụng Thần."},
        {"direction": "Đông", "element": "Mộc", "reason": "Mộc sinh Hỏa — gián tiếp hỗ trợ."},
        {"direction": "Đông Nam", "element": "Mộc", "reason": "Đông Nam thuộc Mộc — sinh Hỏa."},
    ],
    "Thổ": [
        {"direction": "Trung Tâm", "element": "Thổ", "reason": "Trung Tâm thuộc Thổ — hành Dụng Thần."},
        {"direction": "Đông Bắc", "element": "Thổ", "reason": "Đông Bắc thuộc Thổ — hỗ trợ ổn định."},
        {"direction": "Nam", "element": "Hỏa", "reason": "Hỏa sinh Thổ — gián tiếp hỗ trợ."},
    ],
}


def primary_huong_for_dung_than(dung_than: str) -> str:
    """Hướng quý nhân chính — full label (vd. Tây Bắc, không cắt)."""
    rows = HUONG_BY_HANH.get(dung_than, [])
    if not rows:
        return "Trung Tâm"
    return str(rows[0]["direction"])
