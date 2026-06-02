"""
van_trinh_nam_luan_context.py — Build GET /v1/luu-nien/luan-context payload.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from api.version import get_engine_version, utc_now_iso
from engine.can_chi import CAN_HANH, get_can_chi_year
from engine.calendar_month_summary import summarize_calendar_month
from engine.luu_nhat_hours import aggregate_top_hours
from engine.luu_nguyet import get_luu_nguyet_pillar
from engine.luu_nien_luan_a import build_part_a
from engine.month_emphasis import build_month_emphasis
from engine.score_methodology import get_score_methodology_block
from engine.pillars import get_tu_tru
from engine.verdict_signal import (
    element_relation_nhat_chu,
    month_archetype_from_month,
)
from engine.dai_van import get_current_dai_van
from engine.dung_than import find_dung_than
from engine.luu_nien import build_luu_nien
from cache.redis import get_van_trinh_nam_cached, set_van_trinh_nam_cached

_SEED = Path(__file__).resolve().parent.parent.parent / "docs" / "seed"
_WRITING_BRIEF_PATH = _SEED / "van-trinh-nam-writing-brief.json"

_ACTION_NEN = {
    "nang_do": ["chu_dong", "mo_rong"],
    "gieo_hat": ["bat_dau_du_an", "ket_noi"],
    "thu_hoach": ["hoan_tat", "thu_hoach"],
    "phong_thu": ["on_dinh", "tranh_rui_ro"],
    "chuyen_dong": ["linh_hoat", "dieu_chinh"],
}
_ACTION_TRANH = {
    "phong_thu": ["dau_co_lon", "ky_hop_dong_gap"],
    "chuyen_dong": ["thay_doi_dot_ngot"],
}


class VanTrinhNamLuanContextError(Exception):
    """Orchestrator invariant violation."""


def _profile_hash(birth_date_iso: str, birth_time: int, gender: int) -> str:
    raw = f"{birth_date_iso}|{birth_time}|{gender}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _require_twelve_months(months: list) -> list:
    if len(months) != 12:
        raise VanTrinhNamLuanContextError("expected 12 luu_nguyet months")
    return months


def load_van_trinh_nam_writing_brief() -> dict:
    if _WRITING_BRIEF_PATH.exists():
        return json.loads(_WRITING_BRIEF_PATH.read_text(encoding="utf-8"))
    return {"render_order": [], "rules": {}}


def _build_b1(pillar: dict, relation: str, stats: dict) -> dict:
    arch = month_archetype_from_month(
        relation=relation,
        grade_a=stats["grade_a"],
        grade_d=stats["grade_d"],
        layer1_fail=stats["layer1_fail"],
    )
    return {
        "luu_nguyet_display": pillar["display"],
        "nap_am": pillar["nap_am_name"],
        "month_hanh": CAN_HANH[pillar["can_idx"]],
        "element_relation_nhat_chu": relation,
        "month_archetype": arch,
        "fact_bullets_vi": [
            f"Trụ lưu nguyệt: {pillar['display']} ({pillar['nap_am_name']})",
        ],
    }


def _build_b3(cal: dict, top_hours: list[str]) -> dict:
    return {
        "best_days": cal["best_days"],
        "avoid_days": cal["avoid_days"],
        "top_hours": top_hours,
        "calendar_stats": {
            "grade_a": cal["stats"]["grade_a"],
            "grade_b": cal["stats"]["grade_b"],
            "total_days": cal["stats"]["total_days"],
        },
    }


def _build_b4(pillar: dict, relation: str, arch: str) -> dict:
    return {
        "action_tags_nen": _ACTION_NEN.get(arch, ["theo_lich_tot"]),
        "action_tags_tranh": _ACTION_TRANH.get(arch, []),
        "fact_bullets_vi": [f"Tháng {relation.replace('_', ' ')}"],
    }


def build_part_c_hints(months: list[dict]) -> dict:
    archetypes: dict[str, int] = {}
    strong: list[int] = []
    for m in months:
        arch = m["b1_month_theme"]["month_archetype"]
        archetypes[arch] = archetypes.get(arch, 0) + 1
        stats = m["b3_luu_nhat_calendar"].get("calendar_stats", {})
        if stats.get("grade_a", 0) >= 5:
            strong.append(m["month_num"])
    return {
        "synthesis_inputs": {
            "archetype_counts": archetypes,
            "strong_months": strong,
            "month_count": 12,
        },
    }


def build_part_d_mechanics(
    *,
    birth_date_iso: str,
    birth_time: int,
    gender: int,
    year: int,
    luu_nien_raw: dict,
    sample_month: dict,
) -> dict:
    tu_tru = get_tu_tru(birth_date_iso, birth_time)
    dung = find_dung_than(tu_tru)
    ycc = get_can_chi_year(year)
    cur = get_current_dai_van(tu_tru, gender, birth_date_iso, current_date=f"{year}-06-15")
    return {
        "natal": {
            "year": f"{tu_tru['year']['can_name']} {tu_tru['year']['chi_name']}",
            "month": f"{tu_tru['month']['can_name']} {tu_tru['month']['chi_name']}",
            "day": f"{tu_tru['day']['can_name']} {tu_tru['day']['chi_name']}",
            "hour": f"{tu_tru['hour']['can_name']} {tu_tru['hour']['chi_name']}",
            "nhat_chu_hanh": tu_tru["nhat_chu"]["hanh"],
        },
        "dung_than": dung["dung_than"],
        "ky_than": dung["ky_than"],
        "dai_van_current": cur["display"] if cur else None,
        "luu_nien_pillar": luu_nien_raw["year_can_chi"],
        "luu_nguyet_sample_pillar": sample_month["b1_month_theme"]["luu_nguyet_display"],
        "framework_line_vi": (
            "Bát Tự: Tứ trụ bản mệnh, Đại vận 10 năm, Lưu niên năm, "
            "Lưu nguyệt tháng, Lưu nhật chọn ngày."
        ),
    }


def build_van_trinh_nam_luan_context(
    *,
    year: int,
    birth_date_iso: str,
    birth_time: int,
    gender: int,
    use_cache: bool = True,
) -> dict[str, Any]:
    engine_version = get_engine_version()
    phash = _profile_hash(birth_date_iso, birth_time, gender)

    if use_cache:
        cached = get_van_trinh_nam_cached(phash, year, engine_version)
        if cached is not None:
            return cached

    luu_nien_raw = build_luu_nien(
        birth_date_iso=birth_date_iso,
        birth_time=birth_time,
        gender=gender,
        year=year,
    )
    part_a = build_part_a(
        birth_date_iso=birth_date_iso,
        birth_time=birth_time,
        gender=gender,
        year=year,
        luu_raw=luu_nien_raw,
    )
    tu_tru = get_tu_tru(birth_date_iso, birth_time)
    dm_hanh = tu_tru["nhat_chu"]["hanh"]

    months: list[dict] = []
    for m in range(1, 13):
        cal = summarize_calendar_month(
            year, m,
            birth_date_iso=birth_date_iso,
            birth_time=birth_time,
            gender=gender,
        )
        pillar = get_luu_nguyet_pillar(year, m)
        month_hanh = CAN_HANH[pillar["can_idx"]]
        relation = element_relation_nhat_chu(month_hanh, dm_hanh)
        b1 = _build_b1(pillar, relation, cal["stats"])
        arch = b1["month_archetype"]
        top_hours = aggregate_top_hours(cal["scored_days"])
        months.append({
            "month_num": m,
            "target_month": f"{year}-{m:02d}",
            "title_vi": f"Tháng {m}",
            "solar_range": cal["solar_range"],
            "b1_month_theme": b1,
            "b2_month_emphasis": build_month_emphasis(year, m, cal, part_a),
            "b3_luu_nhat_calendar": _build_b3(cal, top_hours),
            "b4_action": _build_b4(pillar, relation, arch),
            "qa_hints": {
                "target_word_band": [80, 120],
                "has_calendar": True,
            },
        })

    months = _require_twelve_months(months)
    payload = {
        "status": "success",
        "meta": {
            "product_title_vi": f"Vận trình năm {year}",
            "year": year,
            "engine_version": engine_version,
            "computed_at": utc_now_iso(),
            "disclaimers": [
                "luu_nguyet_pillar_solar_simplified",
                "not_medical_or_legal_advice",
            ],
        },
        "subject": {
            "birth_date": birth_date_iso,
            "birth_time": birth_time,
            "gender": gender,
        },
        "part_a": part_a,
        "part_b": {"luu_nguyet_months": months},
        "part_c": {"closing_hints": build_part_c_hints(months)},
        "part_d": {"mechanics": build_part_d_mechanics(
            birth_date_iso=birth_date_iso,
            birth_time=birth_time,
            gender=gender,
            year=year,
            luu_nien_raw=luu_nien_raw,
            sample_month=months[0],
        )},
        "score_methodology": get_score_methodology_block(),
        "writing_brief": load_van_trinh_nam_writing_brief(),
    }

    if use_cache:
        set_van_trinh_nam_cached(phash, year, engine_version, payload)
    return payload
