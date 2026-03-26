"""
phi_tinh.py — Cửu cung Phi Tinh (Lưu niên) đơn giản theo năm dương lịch.

Lưới Lạc Thư (từ Đông Nam theo hàng):
  Đông Nam | Nam | Tây Nam
  Đông     | TT  | Tây
  Đông Bắc | Bắc | Tây Bắc

Thứ tự phi thuận (dương niên): sau Trung tâm lần lượt gán vào
Tây Bắc → Tây → Đông Bắc → Nam → Bắc → Tây Nam → Đông → Đông Nam.

Nhập trung: mặc định neo (2024 = 3), mỗi năm giảm 1 (mod 9, 0 → 9);
có thể ghi đè trong docs/seed/phi-tinh-year-center.json.

Giả định & hạn chế: xem docs/algorithm.md §18 và docs/api-spec.md (GET /v1/phong-thuy).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("bat_tu_api.phi_tinh")


class PhiTinhSeedError(Exception):
    """Thiếu hoặc hỏng seed Phi tinh (phi-tinh-stars.json)."""

    def __init__(self, message_vi: str, *, message_en: str | None = None) -> None:
        super().__init__(message_vi)
        self.message_vi = message_vi
        self.message_en = message_en or (
            "Flying Stars seed data is missing or invalid."
        )


# Thứ tự cung sau Trung tâm — thuận phi
PALACES_ORDER: list[str] = [
    "Tây Bắc",
    "Tây",
    "Đông Bắc",
    "Nam",
    "Bắc",
    "Tây Nam",
    "Đông",
    "Đông Nam",
]


def _seed_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "docs" / "seed"


@lru_cache(maxsize=1)
def _load_star_meta_cached() -> dict[str, dict]:
    p = _seed_root() / "phi-tinh-stars.json"
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise PhiTinhSeedError(
            "Thiếu file seed docs/seed/phi-tinh-stars.json — không thể tính Phi Tinh.",
        ) from e
    except json.JSONDecodeError as e:
        raise PhiTinhSeedError(
            f"File phi-tinh-stars.json không hợp lệ (JSON): {e}",
        ) from e
    if not isinstance(data, dict):
        raise PhiTinhSeedError(
            "File phi-tinh-stars.json phải là một object JSON.",
        )
    return data


def load_star_meta() -> dict[str, dict]:
    data = _load_star_meta_cached()
    missing = [str(i) for i in range(1, 10) if str(i) not in data]
    if missing:
        raise PhiTinhSeedError(
            "phi-tinh-stars.json thiếu hoặc không đủ sao 1–9.",
        )
    for k in (str(i) for i in range(1, 10)):
        if not isinstance(data[k], dict):
            raise PhiTinhSeedError(
                f"Sao {k} trong phi-tinh-stars.json phải là object JSON.",
            )
    return data


@lru_cache(maxsize=1)
def _load_year_center_overrides_cached() -> dict[str, int]:
    p = _seed_root() / "phi-tinh-year-center.json"
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning("phi-tinh-year-center.json không có — chỉ dùng công thức nhập trung.")
        return {}
    except json.JSONDecodeError as e:
        logger.warning("phi-tinh-year-center.json lỗi JSON: %s — bỏ qua override.", e)
        return {}
    raw = data.get("overrides", {})
    out: dict[str, int] = {}
    for k, v in raw.items():
        try:
            iv = int(v)
            if 1 <= iv <= 9:
                out[str(k)] = iv
        except (TypeError, ValueError):
            continue
    return out


def load_year_center_overrides() -> dict[str, int]:
    return _load_year_center_overrides_cached()


def annual_center_star(year: int, overrides: dict[str, int] | None = None) -> int:
    """Số sao nhập trung (1–9)."""
    ovr = overrides if overrides is not None else load_year_center_overrides()
    key = str(year)
    if key in ovr:
        return ovr[key]
    d = year - 2024
    c = (3 - d) % 9
    return 9 if c == 0 else c


def is_yang_year_stem(year: int) -> bool:
    """Can năm dương lịch (neo Giáp Tý = 1984): (year-4)%10 chẵn → Dương can."""
    return ((year - 4) % 10) % 2 == 0


def fly_nine_palaces(center: int, forward: bool) -> dict[str, int]:
    """
    Gán sao 1–9 vào 9 cung. Trung tâm = center.
    forward True = thuận phi (+1 mỗi bước), False = nghịch phi.
    """
    grid: dict[str, int] = {"Trung Tâm": center}
    for i, direction in enumerate(PALACES_ORDER, start=1):
        if forward:
            star = ((center - 1 + i) % 9) + 1
        else:
            star = ((center - 1 - i) % 9) + 1
        grid[direction] = star
    return grid


# Thứ tự hiển thị lưới (từ Đông Nam, theo hàng Lạc Thư)
DISPLAY_ORDER: list[str] = [
    "Đông Nam",
    "Nam",
    "Tây Nam",
    "Đông",
    "Trung Tâm",
    "Tây",
    "Đông Bắc",
    "Bắc",
    "Tây Bắc",
]


def build_phi_tinh_payload(year: int) -> dict:
    """
    Trả block phi_tinh đầy đủ cho response API.
    """
    center = annual_center_star(year)
    forward = is_yang_year_stem(year)
    grid = fly_nine_palaces(center, forward)
    stars = load_star_meta()

    phi_list: list[dict] = []
    for direction in DISPLAY_ORDER:
        star_num = grid[direction]
        key = str(star_num)
        meta = stars.get(key, {})
        phi_list.append({
            "direction": direction,
            "star": star_num,
            "star_name": meta.get("star_name", f"Sao {star_num}"),
            "hanh": meta.get("hanh", ""),
            "nature": meta.get("nature", "trung tính"),
            "meaning": meta.get("meaning", ""),
        })

    good_dirs: list[str] = []
    bad_dirs: list[str] = []
    for row in phi_list:
        nat = row["nature"]
        d = row["direction"]
        if nat == "tốt":
            good_dirs.append(d)
        elif nat in ("xấu", "rất xấu"):
            bad_dirs.append(d)

    hoa_giai: list[dict] = []
    for row in phi_list:
        if row["nature"] in ("xấu", "rất xấu"):
            meta = stars.get(str(row["star"]), {})
            remedy = meta.get("remedy_template", "")
            if remedy:
                hoa_giai.append({
                    "direction": row["direction"],
                    "star": row["star"],
                    "remedy": remedy,
                })

    return {
        "phi_tinh_year": year,
        "phi_tinh": phi_list,
        "huong_tot_nam_nay": good_dirs,
        "huong_xau_nam_nay": bad_dirs,
        "hoa_giai": hoa_giai,
        "phi_tinh_note_vi": (
            "Hướng tốt/xấu năm nay xếp theo tính chất sao lưu niên trong seed — "
            "không lọc theo Dụng Thần / Kỵ Thần cá nhân. "
            "Năm và thuận/nghịch phi theo quy ước dương lịch đơn giản; có thể lệch sách dùng Lập Xuân."
        ),
    }
