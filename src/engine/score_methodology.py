"""
Direction C score methodology — static contract for NLTT consumers.
"""

from __future__ import annotations

from typing import Any

DIRECTION_C_SOURCES: list[dict[str, Any]] = [
    {"ref": 1, "label_vi": "Trực ngày", "description_vi": "Thập nhị trực trong tháng âm lịch"},
    {"ref": 2, "label_vi": "Nhị thập bát tú", "description_vi": "Sao ngày theo lịch truyền thống"},
    {"ref": 3, "label_vi": "Can chi · lá số", "description_vi": "Quan hệ ngũ hành ngày với lá số cá nhân"},
    {"ref": 4, "label_vi": "Giờ vàng", "description_vi": "Khung giờ Hoàng đạo phù hợp với lá số"},
]

SCORE_METHODOLOGY: dict[str, Any] = {
    "summary_vi": "Điểm tổng hợp từ Trực, sao, Can Chi với lá số, và giờ vàng.",
    "weights": [
        {"factor": "truc", "label_vi": "Trực ngày", "max_points": 30},
        {"factor": "sao28", "label_vi": "Nhị thập bát tú", "max_points": 25},
        {"factor": "can_chi_laso", "label_vi": "Can chi · lá số", "max_points": 25},
        {"factor": "gio_vang", "label_vi": "Giờ vàng", "max_points": 20},
    ],
}

# BASE_SCORE 50 split across presentation buckets (no client-visible base row)
BASE_BUCKET_SPLIT = {"truc": 19, "sao28": 16, "can_chi_laso": 15}


def get_score_methodology_block() -> dict[str, Any]:
    return {
        "score_max": 100,
        "score_methodology": dict(SCORE_METHODOLOGY),
    }
