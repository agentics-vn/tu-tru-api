"""
Direction C day-score presentation — 4-factor breakdown for NLTT.
"""

from __future__ import annotations

from typing import Any, Optional

from engine.score_methodology import DIRECTION_C_SOURCES
from filter import INTENT_LABELS

_FACTOR_ORDER = ("truc", "sao28", "can_chi_laso", "gio_vang")
_SOURCE_BY_ID = {
    "truc": DIRECTION_C_SOURCES[0],
    "sao28": DIRECTION_C_SOURCES[1],
    "can_chi_laso": DIRECTION_C_SOURCES[2],
    "gio_vang": DIRECTION_C_SOURCES[3],
}


def _intent_label(intent: str) -> str:
    return INTENT_LABELS.get(intent, intent)


def _points_phrase(points: int) -> str:
    if points > 0:
        return f"cộng {points} điểm"
    if points < 0:
        return f"trừ {abs(points)} điểm"
    return "không đổi điểm"


def _truc_type(day_info: dict) -> str:
    truc = day_info.get("truc_name", "")
    score = day_info.get("truc_score", 0)
    if score >= 2:
        quality = "Thuận"
    elif score >= 0:
        quality = "Trung"
    else:
        quality = "Bất lợi"
    return f"{quality} · Trực {truc}"


def _sao28_type(star_info: dict, sao_28: dict) -> str:
    hd = "Hoàng Đạo" if star_info.get("is_hoang_dao") else "Hắc Đạo"
    star = star_info.get("star_name", "")
    sao_name = sao_28.get("name", "")
    if sao_name:
        return f"{hd} · {star} · Sao {sao_name}"
    return f"{hd} · {star}"


def _can_chi_type(day_info: dict, user_chart: dict) -> str:
    day_hanh = day_info.get("day_nap_am_hanh", "")
    can_chi = f"{day_info.get('day_can_name', '')} {day_info.get('day_chi_name', '')}".strip()
    if user_chart.get("dung_than"):
        dm = user_chart.get("nhat_chu", {}).get("can_name", "Nhật Chủ")
        if day_hanh == user_chart.get("dung_than"):
            rel = "Dụng Thần"
        elif day_hanh == user_chart.get("hi_than"):
            rel = "Hỷ Thần"
        elif day_hanh == user_chart.get("ky_than_v2"):
            rel = "Kỵ Thần"
        elif day_hanh == user_chart.get("cuu_than"):
            rel = "Cừu Thần"
        else:
            rel = "Trung hòa"
        return f"{can_chi} · {rel} ({dm})"
    menh = user_chart.get("menh_name", "mệnh")
    if day_hanh == user_chart.get("duong_than"):
        return f"{can_chi} · Dương Thần ({menh})"
    return f"{can_chi} · {day_hanh}"


def _gio_vang_type(gio_tot: list[dict]) -> str:
    if not gio_tot:
        return "Không có giờ Hoàng đạo nổi bật"
    names = [g.get("chi_name", "") for g in gio_tot[:2]]
    return "Giờ vàng · " + ", ".join(n for n in names if n)


def _reason_truc(
    day_info: dict,
    points: int,
    intent: str,
    personalized: bool,
    user_chart: dict,
) -> str:
    truc = day_info.get("truc_name", "")
    pts = _points_phrase(points)
    base = f"Trực {truc} {pts} trong tổng điểm ngày."
    if personalized and user_chart.get("dung_than"):
        intent_vi = _intent_label(intent).lower()
        base += f" Với lá số của bạn, Trực này {'hỗ trợ' if points >= 0 else 'hạn chế'} việc {intent_vi}."
    elif personalized:
        base += f" So với mệnh {user_chart.get('menh_name', '')}, Trực này {'thuận' if points >= 0 else 'cần cân nhắc'}."
    return base


def _reason_sao28(
    star_info: dict,
    sao_28: dict,
    points: int,
    intent: str,
    personalized: bool,
) -> str:
    hd = "Hoàng Đạo" if star_info.get("is_hoang_dao") else "Hắc Đạo"
    sao = sao_28.get("name", "")
    pts = _points_phrase(points)
    text = f"Ngày {hd} ({star_info.get('star_name', '')})"
    if sao:
        text += f", sao {sao} ({sao_28.get('tot_xau', '')})"
    text += f" {pts}."
    if personalized:
        text += f" Ảnh hưởng này được tính cho mục đích {_intent_label(intent).lower()}."
    return text


def _reason_can_chi_laso(
    day_info: dict,
    user_chart: dict,
    points: int,
    intent: str,
    personalized: bool,
) -> str:
    day_hanh = day_info.get("day_nap_am_hanh", "")
    pts = _points_phrase(points)
    if not personalized:
        return (
            f"Nạp Âm ngày hành {day_hanh} {pts} — "
            f"đánh giá theo lịch chung, chưa cá nhân hoá lá số."
        )
    if user_chart.get("dung_than"):
        dm = user_chart.get("nhat_chu", {}).get("can_name", "Nhật Chủ")
        dung = user_chart.get("dung_than", "")
        if day_hanh == dung:
            return (
                f"Hành {day_hanh} của ngày trùng Dụng Thần ({dung}) của Nhật Chủ {dm}, "
                f"{pts} — rất thuận cho sức khỏe và việc quan trọng."
            )
        if day_hanh == user_chart.get("ky_than_v2"):
            return (
                f"Hành {day_hanh} là Kỵ Thần của Nhật Chủ {dm}, {pts} — "
                f"nên cân nhắc khi chọn ngày cho {_intent_label(intent).lower()}."
            )
        return (
            f"Quan hệ ngũ hành ngày ({day_hanh}) với lá số Nhật Chủ {dm} {pts} "
            f"trong bối cảnh {_intent_label(intent).lower()}."
        )
    menh = user_chart.get("menh_name", "")
    if day_hanh == user_chart.get("duong_than"):
        return (
            f"Nạp Âm ngày là Dương Thần của mệnh {menh}, {pts} — "
            f"hỗ trợ năng lượng tích cực cho bạn."
        )
    return (
        f"Can Chi ngày hành {day_hanh} so với mệnh {menh} {pts}; "
        f"xem thêm chi tiết trong lá số."
    )


def _reason_gio_vang(
    gio_tot: list[dict],
    points: int,
    user_chart: dict,
    personalized: bool,
) -> str:
    pts = _points_phrase(points)
    if personalized and user_chart.get("dung_than"):
        dung = user_chart.get("dung_than", "")
        text = (
            f"Phần giờ vàng {pts} phản ánh khung Hoàng đạo hợp Dụng Thần hành {dung} "
            f"của bạn — nên ưu tiên khởi sự trong các giờ tốt."
        )
    elif personalized:
        text = (
            f"Phần giờ vàng {pts} — các khung Hoàng đạo trong ngày phù hợp năng lượng lá số của bạn."
        )
    else:
        text = f"Phần giờ vàng {pts} — đánh giá khung giờ tốt theo lịch chung."
    if gio_tot:
        sample = gio_tot[0]
        text += (
            f" Giờ đáng chú ý: {sample.get('chi_name', '')} "
            f"({sample.get('start', '')}–{sample.get('end', '')})."
        )
    return text


def build_direction_c_breakdown(
    *,
    day_info: dict,
    user_chart: dict,
    intent: str,
    presentation_buckets: dict[str, int],
    star_info: dict,
    sao_28: dict,
    gio_tot: list[dict],
    personalized: bool = True,
) -> list[dict[str, Any]]:
    """Build exactly 4 breakdown items; sum(points) == score via gio_vang residual."""
    types = {
        "truc": _truc_type(day_info),
        "sao28": _sao28_type(star_info, sao_28),
        "can_chi_laso": _can_chi_type(day_info, user_chart if personalized else {}),
        "gio_vang": _gio_vang_type(gio_tot),
    }
    reasons = {
        "truc": _reason_truc(day_info, presentation_buckets["truc"], intent, personalized, user_chart),
        "sao28": _reason_sao28(star_info, sao_28, presentation_buckets["sao28"], intent, personalized),
        "can_chi_laso": _reason_can_chi_laso(
            day_info, user_chart, presentation_buckets["can_chi_laso"], intent, personalized
        ),
        "gio_vang": _reason_gio_vang(
            gio_tot, presentation_buckets["gio_vang"], user_chart, personalized
        ),
    }

    items: list[dict[str, Any]] = []
    for fid in _FACTOR_ORDER:
        src = _SOURCE_BY_ID[fid]
        items.append({
            "id": fid,
            "source": src["label_vi"],
            "source_ref": src["ref"],
            "type": types[fid],
            "points": presentation_buckets[fid],
            "reason_vi": reasons[fid],
        })
    return items


def build_compare_copy(
    score_a: int,
    score_b: int,
    date_a: str,
    date_b: str,
    intent: str,
) -> tuple[str, list[str]]:
    """Facts-only comparison prose for day-compare."""
    delta = score_b - score_a
    intent_vi = _intent_label(intent).lower()
    if delta > 0:
        comparison = (
            f"Ngày {date_b} cao hơn {date_a} {delta} điểm "
            f"cho {intent_vi} (điểm {score_b} so với {score_a})."
        )
        better = [f"Ưu tiên {date_b} nếu linh hoạt thời gian"]
    elif delta < 0:
        comparison = (
            f"Ngày {date_a} cao hơn {date_b} {abs(delta)} điểm "
            f"cho {intent_vi} (điểm {score_a} so với {score_b})."
        )
        better = [f"Ưu tiên {date_a} nếu linh hoạt thời gian"]
    else:
        comparison = f"Hai ngày bằng điểm ({score_a}) cho {intent_vi}."
        better = ["Cân nhắc tiện lợi thực tế hoặc giờ vàng"]
    return comparison, better
