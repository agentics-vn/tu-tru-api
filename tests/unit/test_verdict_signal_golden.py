"""Semantic golden matrix for verdict_signal / month_archetype."""

from __future__ import annotations

from engine.verdict_signal import (
    month_archetype_from_month,
    verdict_signal_from_year,
)


def test_khac_menh_bad_stats_not_thu_hoach():
    arch = month_archetype_from_month(
        relation="khắc_menh",
        grade_a=1,
        grade_d=10,
        layer1_fail=12,
    )
    assert arch != "thu_hoach"
    assert arch == "phong_thu"
    vs = verdict_signal_from_year("khắc_menh", "xấu")
    assert vs == "than_trong"


def test_sinh_menh_many_a_thuan_archetype():
    vs = verdict_signal_from_year("sinh_menh", "tốt")
    assert vs == "thuan"
    arch = month_archetype_from_month(
        relation="sinh_menh",
        grade_a=8,
        grade_d=0,
        layer1_fail=0,
    )
    assert arch in ("nang_do", "gieo_hat")


def test_ky_than_emphasis_signal_up():
    from engine.month_emphasis import _month_vs_year_delta

    signal, tags = _month_vs_year_delta(
        "suc_khoe",
        "Kim",
        nhat_chu_hanh="Thổ",
        year_rel="sinh_menh",
        dung_than="Mộc",
        ky_than="Kim",
        stats={"grade_a": 5, "grade_d": 0},
    )
    assert signal == "up"
    assert "ky_than_match" in tags
