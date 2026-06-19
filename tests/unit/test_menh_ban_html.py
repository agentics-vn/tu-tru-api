"""Unit tests for Mệnh Bàn HTML renderer."""

from __future__ import annotations

from engine.chart_bundle import build_full_chart
from engine.menh_ban_html import render_menh_ban_html
from engine.pillars import get_tu_tru


def _chart(**kwargs):
    tu_tru = get_tu_tru("1990-03-21", 6)
    defaults = dict(
        birth_date="1990-03-21",
        gender=1,
        birth_time_slot=6,
        birth_minute=15,
        view_year=2026,
    )
    defaults.update(kwargs)
    return build_full_chart(tu_tru, **defaults)


def test_html_contains_core_sections():
    html_out = render_menh_ban_html(_chart(name="NGUYỄN VĂN T"))
    assert '<div class="mbtt">' in html_out
    assert "Mệnh Bàn Tứ Trụ" in html_out
    assert "NGUYỄN VĂN T" in html_out
    assert "Canh" in html_out and "Ngọ" in html_out
    assert "Đại Vận" in html_out
    assert "Lưu Niên" in html_out
    assert "Thần Sát Nguyên Cục" in html_out
    assert "Xuân Phân" in html_out


def test_html_escapes_name():
    html_out = render_menh_ban_html(_chart(name='<script>alert("x")</script>'))
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out


def test_html_highlights_view_year():
    html_out = render_menh_ban_html(_chart())
    assert "mbtt-hl" in html_out
    assert "Bính" in html_out
