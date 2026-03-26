"""
phong_thuy.py — Gợi ý phong thủy theo Dụng Thần + mục đích + cường nhược + Phi Tinh.

Bảng hướng/màu/số/vật cố định theo hành; mục đích lấy từ docs/seed/phong-thuy-purposes.json.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from engine.cuong_nhuoc import analyze_chart_strength
from engine.dung_than import KHAC_TARGET, SINH_BY, SINH_TARGET

# ─────────────────────────────────────────────────────────────────────────────
# Lookup tables (cố định theo hành)
# ─────────────────────────────────────────────────────────────────────────────

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

MAU_BY_HANH: dict[str, list[dict]] = {
    "Kim": [
        {"color": "Trắng", "hex": "#F5F5F5", "element": "Kim"},
        {"color": "Bạc", "hex": "#C0C0C0", "element": "Kim"},
        {"color": "Vàng nhạt", "hex": "#F0E68C", "element": "Thổ"},
    ],
    "Mộc": [
        {"color": "Xanh lá", "hex": "#3A6B35", "element": "Mộc"},
        {"color": "Xanh dương", "hex": "#2B6CB0", "element": "Thủy"},
        {"color": "Đen", "hex": "#1A1A1A", "element": "Thủy"},
    ],
    "Thủy": [
        {"color": "Đen", "hex": "#1A1A1A", "element": "Thủy"},
        {"color": "Xanh dương", "hex": "#2B6CB0", "element": "Thủy"},
        {"color": "Trắng", "hex": "#F5F5F5", "element": "Kim"},
    ],
    "Hỏa": [
        {"color": "Đỏ", "hex": "#C53030", "element": "Hỏa"},
        {"color": "Tím", "hex": "#6B46C1", "element": "Hỏa"},
        {"color": "Xanh lá", "hex": "#3A6B35", "element": "Mộc"},
    ],
    "Thổ": [
        {"color": "Vàng đất", "hex": "#B8860B", "element": "Thổ"},
        {"color": "Nâu", "hex": "#8B6914", "element": "Thổ"},
        {"color": "Đỏ", "hex": "#C53030", "element": "Hỏa"},
    ],
}

SO_BY_HANH: dict[str, list[int]] = {
    "Kim": [4, 9],
    "Mộc": [1, 2, 6],
    "Thủy": [1, 6],
    "Hỏa": [2, 7],
    "Thổ": [5, 0, 8],
}

VAT_PHAM_BY_HANH: dict[str, list[dict]] = {
    "Kim": [
        {"item": "Chuông gió kim loại", "element": "Kim", "reason": "Tăng cường Kim khí — tốt cho tài lộc."},
        {"item": "Tượng rùa đồng", "element": "Kim", "reason": "Kim khí hỗ trợ sự nghiệp ổn định."},
    ],
    "Mộc": [
        {"item": "Cây xanh để bàn", "element": "Mộc", "reason": "Tăng cường Mộc khí — tốt cho tài lộc và sức khỏe."},
        {"item": "Bể cá nhỏ", "element": "Thủy", "reason": "Thủy sinh Mộc — kích hoạt dòng tiền lưu thông."},
        {"item": "Tranh phong cảnh rừng", "element": "Mộc", "reason": "Tăng Mộc khí trong không gian làm việc."},
    ],
    "Thủy": [
        {"item": "Bể cá phong thủy", "element": "Thủy", "reason": "Tăng cường Thủy khí — kích hoạt tài lộc."},
        {"item": "Thác nước mini", "element": "Thủy", "reason": "Nước chảy liên tục tượng trưng cho tiền bạc."},
    ],
    "Hỏa": [
        {"item": "Đèn muối Himalaya", "element": "Hỏa", "reason": "Ánh sáng ấm tăng Hỏa khí — tốt cho năng lượng."},
        {"item": "Nến thơm", "element": "Hỏa", "reason": "Lửa tượng trưng cho sự sáng tạo và nhiệt huyết."},
    ],
    "Thổ": [
        {"item": "Chậu đá cảnh", "element": "Thổ", "reason": "Đá thuộc Thổ — tăng sự ổn định."},
        {"item": "Bình gốm sứ", "element": "Thổ", "reason": "Gốm sứ thuộc Thổ — hỗ trợ sức khỏe."},
    ],
}

PURPOSE_CODES = frozenset({"NHA_O", "VAN_PHONG", "CUA_HANG", "PHONG_KHACH"})
DEFAULT_PURPOSE = "NHA_O"


class PhongThuySeedError(Exception):
    """Thiếu hoặc hỏng seed phong thủy (mục đích / hóa giải cặp đôi)."""

    def __init__(self, message_vi: str, *, message_en: str | None = None) -> None:
        super().__init__(message_vi)
        self.message_vi = message_vi
        self.message_en = message_en or (
            "Feng shui seed data is missing or invalid."
        )


def _seed_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "docs" / "seed"


@lru_cache(maxsize=1)
def _load_purposes() -> dict[str, Any]:
    p = _seed_root() / "phong-thuy-purposes.json"
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise PhongThuySeedError(
            "Thiếu file seed docs/seed/phong-thuy-purposes.json — không thể tải mục đích phong thủy.",
        ) from e
    except json.JSONDecodeError as e:
        raise PhongThuySeedError(
            f"File phong-thuy-purposes.json không hợp lệ (JSON): {e}",
        ) from e
    if not isinstance(data, dict):
        raise PhongThuySeedError(
            "phong-thuy-purposes.json phải là object JSON.",
        )
    return data


@lru_cache(maxsize=1)
def _load_couple_remedies() -> dict[str, Any]:
    p = _seed_root() / "phong-thuy-couple-remedies.json"
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise PhongThuySeedError(
            "Thiếu file seed docs/seed/phong-thuy-couple-remedies.json — không thể tải hóa giải cặp đôi.",
        ) from e
    except json.JSONDecodeError as e:
        raise PhongThuySeedError(
            f"File phong-thuy-couple-remedies.json không hợp lệ (JSON): {e}",
        ) from e
    if not isinstance(data, dict):
        raise PhongThuySeedError(
            "phong-thuy-couple-remedies.json phải là object JSON.",
        )
    return data


def huong_xau_labeled(ky_than: str) -> list[dict]:
    huong_xau = HUONG_BY_HANH.get(ky_than, [])
    return [
        {**h, "reason": f"{h['element']} là Kỵ Thần — nên tránh hướng này."}
        for h in huong_xau
    ]


def build_purpose_payload(purpose: str, dung_than: str) -> tuple[list[dict], dict[str, Any]]:
    """
    Vật phẩm theo mục đích + các gợi ý bổ sung (huong_ngoi, quay_thu_ngan, phong_khach).
    """
    purposes = _load_purposes()
    p = purpose if purpose in PURPOSE_CODES else DEFAULT_PURPOSE
    block = purposes.get(p, {}).get(dung_than, {})
    pur_vat = block.get("vat_pham")
    if isinstance(pur_vat, list) and len(pur_vat) > 0:
        vat_pham = pur_vat
    else:
        vat_pham = list(VAT_PHAM_BY_HANH.get(dung_than, []))

    extras: dict[str, Any] = {}
    for key in ("huong_ngoi", "quay_thu_ngan", "phong_khach"):
        if key in block:
            extras[key] = block[key]
    return vat_pham, extras


def build_personalization(
    tu_tru: Optional[dict],
    dung_than: str,
) -> Optional[dict[str, Any]]:
    """Theo cường nhược; None nếu không có Tứ Trụ."""
    if tu_tru is None:
        return None
    st = analyze_chart_strength(tu_tru)
    strength = st["strength"]
    sinh_hanh = SINH_BY.get(dung_than)

    if strength == "nhược":
        intensity = "mạnh"
        note = (
            f"Lá số thiên nhược — nên ưu tiên bổ sung hành {dung_than} mạnh mẽ."
        )
        extra_items: list[dict] = []
        if sinh_hanh:
            src = VAT_PHAM_BY_HANH.get(sinh_hanh, [])
            for row in src[:2]:
                extra_items.append({
                    "item": row["item"],
                    "element": row["element"],
                    "reason": (
                        f"{row['element']} sinh {dung_than} — bổ trợ thêm khi mệnh nhược "
                        f"({row.get('reason', '')})"
                    ).strip(),
                })
        return {
            "chart_strength": strength,
            "intensity": intensity,
            "note": note,
            "extra_items": extra_items,
        }

    if strength == "vượng":
        return {
            "chart_strength": strength,
            "intensity": "nhẹ",
            "note": (
                "Lá số thiên vượng — chỉ cần bổ sung nhẹ, tránh quá dư thừa cùng một hành."
            ),
            "extra_items": [],
        }

    return {
        "chart_strength": strength,
        "intensity": "vừa",
        "note": "Lá số cân bằng — duy trì phong thủy hiện tại là tốt.",
        "extra_items": [],
    }


def build_couple_harmony(
    h1: str,
    h2: str,
    *,
    person1_menh_name: str | None = None,
    person2_menh_name: str | None = None,
) -> Optional[dict[str, Any]]:
    """
    Chỉ trả khi hai Nạp Âm hành có quan hệ tương khắc trực tiếp (hành này khắc hành kia).
    """
    if h1 == h2:
        return None

    if KHAC_TARGET.get(h1) == h2:
        attacker, victim = h1, h2
    elif KHAC_TARGET.get(h2) == h1:
        attacker, victim = h2, h1
    else:
        return None

    remedy_el = SINH_TARGET[attacker]
    rel = f"Tương Khắc ({attacker} khắc {victim})"
    explanation = (
        f"{remedy_el} là hành trung gian — {attacker} sinh {remedy_el}, "
        f"{remedy_el} sinh {victim} — hóa giải xung khắc."
    )

    pack = _load_couple_remedies().get(remedy_el, {})
    remedies = pack.get("remedies", [])
    colors = pack.get("colors_for_shared_space", [])
    suffix = pack.get("explanation_suffix", "")

    out: dict[str, Any] = {
        "person1_hanh": h1,
        "person2_hanh": h2,
        "relation": rel,
        "remedy_element": remedy_el,
        "explanation": f"{explanation} {suffix}".strip(),
        "remedies": remedies,
        "colors_for_shared_space": colors,
    }
    if person1_menh_name is not None:
        out["person1_menh_name"] = person1_menh_name
    if person2_menh_name is not None:
        out["person2_menh_name"] = person2_menh_name
    return out
