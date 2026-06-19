"""
menh_ban_html.py — Self-contained HTML fragment for Mệnh Bàn Tứ Trụ grid.

Renders the same layout as web/components/MenhBanTuTru.tsx using inline CSS
for CMS/article embed (no React/Tailwind).

Source: docs/algorithm.md §22.11
"""

from __future__ import annotations

import html
from typing import Any

_PILLAR_KEYS = ("year", "month", "day", "hour")
_PILLAR_LABELS = {"year": "Năm", "month": "Tháng", "day": "Ngày", "hour": "Giờ"}
_THAN_SAT_HEADERS = ("Niên Thần", "Nguyệt Thần", "Nhật Thần", "Thời Thần")

_HANH_COLOR: dict[str, str] = {
    "Mộc": "#2f6f4f",
    "Hỏa": "#a3201f",
    "Thổ": "#9a7c22",
    "Kim": "#6f6a52",
    "Thủy": "#274b6d",
}

_MBTT_CSS = """
.mbtt{--paper:#f0ece2;--paper-warm:#ede7d3;--ink:#18150e;--muted:#7a7050;
--gold:#c5a55a;--gold-deep:#9a7c22;--vermilion:#a3201f;--jade:#5e7d5e;
--hairline:rgba(154,124,34,0.30);--gold-hl:rgba(197,165,90,0.30);
font-family:Georgia,"Times New Roman",serif;color:var(--ink);max-width:56rem;margin:0 auto}
.mbtt *{box-sizing:border-box}
.mbtt-card{background:var(--paper);border:1px solid var(--gold);border-radius:8px;
box-shadow:0 4px 12px rgba(14,28,20,0.08);margin-bottom:1rem;overflow:hidden}
.mbtt-p4{padding:1rem}
.mbtt-header{display:grid;gap:1rem;padding:1.25rem}
@media(min-width:768px){.mbtt-header{grid-template-columns:1fr 1fr}}
.mbtt-brand{font-family:"Arial Narrow",system-ui,sans-serif;font-size:11px;
letter-spacing:0.3em;text-transform:uppercase;color:var(--gold-deep);margin:0}
.mbtt-title{font-family:"Arial Narrow",system-ui,sans-serif;font-size:1.75rem;
font-weight:700;letter-spacing:0.05em;color:var(--vermilion);margin:0.25rem 0 0}
.mbtt-name{font-size:1.125rem;font-weight:600;margin:0.5rem 0 0}
.mbtt-meta{display:grid;grid-template-columns:auto 1fr;gap:0.35rem 0.75rem;font-size:0.875rem}
.mbtt-meta dt{font-family:"Arial Narrow",system-ui,sans-serif;text-transform:uppercase;
letter-spacing:0.05em;color:var(--muted);margin:0}
.mbtt-meta dd{margin:0}
.mbtt-khoi{font-weight:600;color:var(--vermilion)}
.mbtt-section{font-family:"Arial Narrow",system-ui,sans-serif;font-size:0.875rem;
font-weight:600;text-transform:uppercase;letter-spacing:0.15em;color:var(--jade);margin:0 0 0.5rem}
.mbtt-scroll{overflow-x:auto}
.mbtt-table{width:100%;border-collapse:collapse;min-width:640px}
.mbtt-table--wide{min-width:680px}
.mbtt-table td,.mbtt-table th{border:1px solid var(--hairline);padding:0.5rem;
text-align:center;vertical-align:middle}
.mbtt-row-label{width:6rem;text-align:left!important;background:var(--paper-warm);
font-family:"Arial Narrow",system-ui,sans-serif;font-size:11px;font-weight:600;
text-transform:uppercase;letter-spacing:0.04em;color:var(--vermilion);vertical-align:middle}
.mbtt-col-head{background:var(--paper-warm);font-family:"Arial Narrow",system-ui,sans-serif;
font-size:0.875rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--jade)}
.mbtt-pillar{background:rgba(237,231,211,0.6)}
.mbtt-can{font-family:"Arial Narrow",system-ui,sans-serif;font-size:1.75rem;
font-weight:700;line-height:1.2}
.mbtt-nhat{font-family:"Arial Narrow",system-ui,sans-serif;font-weight:700;
text-transform:uppercase;color:var(--vermilion)}
.mbtt-age{color:var(--vermilion)}
.mbtt-muted{color:var(--muted)}
.mbtt-hl{background:var(--gold-hl)}
.mbtt-stars{text-align:center;font-size:0.875rem}
.mbtt-stars span{display:block;line-height:1.4}
"""


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _format_dmy(iso: str) -> str:
    parts = iso.split("-")
    if len(parts) != 3:
        return iso
    y, m, d = parts
    return f"{int(d)}/{int(m)}/{y}"


def _hanh_span(text: str, hanh: str, *, large: bool = False) -> str:
    color = _HANH_COLOR.get(hanh, "var(--ink)")
    size = "1.75rem" if large else "inherit"
    family = "Arial Narrow,system-ui,sans-serif" if large else "inherit"
    weight = "700" if large else "600"
    return (
        f'<span style="color:{color};font-size:{size};'
        f'font-family:{family};font-weight:{weight}">{_esc(text)}</span>'
    )


def render_menh_ban_html(chart: dict[str, Any]) -> str:
    """Return embeddable HTML fragment (with scoped <style>) for a menh_ban payload."""
    h = chart["header"]
    pillars = chart["pillars"]

    parts: list[str] = [
        '<div class="mbtt">',
        f"<style>{_MBTT_CSS}</style>",
        '<div class="mbtt-card"><div class="mbtt-header">',
        '<div>',
        '<p class="mbtt-brand">Luận Giải Bát Tự</p>',
        '<h2 class="mbtt-title">Mệnh Bàn Tứ Trụ</h2>',
        f'<p class="mbtt-name">{_esc(h.get("name") or "—")}</p>',
        "</div>",
        "<dl class=\"mbtt-meta\">",
        f"<dt>Giới tính</dt><dd>{_esc(h.get('gender_label', ''))}</dd>",
        f"<dt>Dương lịch</dt><dd>{_esc(h.get('duong_lich_display', ''))}</dd>",
        f"<dt>Âm lịch</dt><dd>{_esc(h['am_lich']['display'])}</dd>",
        f"<dt>Tiết khí</dt><dd>{_esc(h['tiet_khi']['name'])} "
        f"(nguyệt lệnh {_esc(h.get('nguyet_lenh', ''))})</dd>",
        f"<dt>Khởi vận</dt><dd class=\"mbtt-khoi\">"
        f"{_esc(_format_dmy(h['khoi_van_date']))}</dd>",
        "</dl></div></div>",
        '<div class="mbtt-card mbtt-scroll"><table class="mbtt-table"><thead><tr>',
        '<th class="mbtt-row-label"> </th>',
    ]

    for pk in _PILLAR_KEYS:
        parts.append(f'<th class="mbtt-col-head">{_PILLAR_LABELS[pk]}</th>')
    parts.append("</tr></thead><tbody>")

    # Thập Thần
    parts.append("<tr><th class=\"mbtt-row-label\">Thập Thần</th>")
    for pk in _PILLAR_KEYS:
        label = pillars[pk]["thap_than"]["short_label"]
        if pk == "day":
            cell = f'<span class="mbtt-nhat">{_esc(label)}</span>'
        else:
            cell = _esc(label)
        parts.append(f"<td>{cell}</td>")
    parts.append("</tr>")

    # Bát Tự
    parts.append("<tr><th class=\"mbtt-row-label\">Bát Tự</th>")
    for pk in _PILLAR_KEYS:
        p = pillars[pk]
        parts.append(
            f'<td class="mbtt-pillar"><div class="mbtt-can">'
            f'{_hanh_span(p["can"]["name"], p["can"]["hanh"], large=True)}<br>'
            f'{_hanh_span(p["chi"]["name"], p["chi"]["hanh"], large=True)}'
            f"</div></td>"
        )
    parts.append("</tr>")

    # Nạp Âm
    parts.append("<tr><th class=\"mbtt-row-label\">Nạp Âm Ngũ Hành</th>")
    for pk in _PILLAR_KEYS:
        parts.append(f"<td>{_esc(pillars[pk]['nap_am']['name'])}</td>")
    parts.append("</tr>")

    # Tàng ẩn
    parts.append("<tr><th class=\"mbtt-row-label\">Can Chi Tàng Ẩn</th>")
    for pk in _PILLAR_KEYS:
        spans = " ".join(
            _hanh_span(t["can_name"], t["hanh"])
            for t in pillars[pk]["tang_can"]
        )
        parts.append(f"<td>{spans}</td>")
    parts.append("</tr>")

    # Phó tinh
    parts.append("<tr><th class=\"mbtt-row-label\">Phó Tinh</th>")
    for pk in _PILLAR_KEYS:
        labels = "  ".join(p["short_label"] for p in pillars[pk]["pho_tinh"])
        parts.append(f"<td>{_esc(labels)}</td>")
    parts.append("</tr>")

    # Trường sinh
    parts.append("<tr><th class=\"mbtt-row-label\">Thập Nhị Thần</th>")
    for pk in _PILLAR_KEYS:
        parts.append(f"<td>{_esc(pillars[pk]['truong_sinh']['label_vi'])}</td>")
    parts.append("</tr></tbody></table></div>")

    # Đại Vận
    parts.append(
        '<div class="mbtt-card mbtt-p4 mbtt-scroll">'
        '<p class="mbtt-section">Đại Vận</p>'
        '<table class="mbtt-table mbtt-table--wide"><tbody><tr>'
    )
    for c in chart["dai_van"]["cycles"]:
        can, _, chi = c["display"].partition(" ")
        parts.append(
            f'<td><div class="mbtt-can" style="font-size:1rem">'
            f"{_esc(can)}<br>{_esc(chi)}</div></td>"
        )
    parts.append("</tr><tr>")
    for c in chart["dai_van"]["cycles"]:
        parts.append(
            f'<td style="font-size:0.75rem">'
            f'<div class="mbtt-age">{_esc(c["age_label"])}</div>'
            f'<div class="mbtt-muted">{c["start_year"]}</div></td>'
        )
    parts.append("</tr></tbody></table></div>")

    # Lưu Niên
    parts.append(
        '<div class="mbtt-card mbtt-p4 mbtt-scroll">'
        '<p class="mbtt-section">Lưu Niên</p>'
        '<table class="mbtt-table mbtt-table--wide"><tbody><tr>'
    )
    for row in chart["luu_nien"]:
        hl = "mbtt-hl" if row.get("selected") else ""
        can, _, chi = row["display"].partition(" ")
        parts.append(
            f'<td class="mbtt-can {hl}" style="font-size:1rem">'
            f"{_esc(can)}<br>{_esc(chi)}</td>"
        )
    parts.append("</tr><tr>")
    for row in chart["luu_nien"]:
        hl = "mbtt-hl" if row.get("selected") else ""
        parts.append(
            f'<td class="{hl}" style="font-size:0.75rem">'
            f'<div class="mbtt-age">{row["year"]}</div>'
            f'<div class="mbtt-muted">{_esc(row["age_label"])}</div></td>'
        )
    parts.append("</tr></tbody></table></div>")

    # Thần Sát
    parts.append(
        '<div class="mbtt-card mbtt-p4">'
        '<p class="mbtt-section">Thần Sát Nguyên Cục</p>'
        '<table class="mbtt-table"><thead><tr>'
    )
    for label in _THAN_SAT_HEADERS:
        parts.append(f'<th class="mbtt-col-head">{label}</th>')
    parts.append("</tr></thead><tbody><tr>")
    for pk in _PILLAR_KEYS:
        stars = pillars[pk]["than_sat"]
        if stars:
            inner = "".join(
                f"<span>{_esc(s['name'])}</span>" for s in stars
            )
            parts.append(f'<td class="mbtt-stars">{inner}</td>')
        else:
            parts.append('<td class="mbtt-muted">—</td>')
    parts.append("</tr></tbody></table></div>")

    # Mệnh
    parts.append(
        '<div class="mbtt-card mbtt-p4">'
        '<p class="mbtt-section">Mệnh</p>'
        '<table class="mbtt-table"><thead><tr>'
        '<th class="mbtt-col-head">Mệnh Cung</th>'
        '<th class="mbtt-col-head">Thai Nguyên</th>'
        '<th class="mbtt-col-head">Niên Không</th>'
        '<th class="mbtt-col-head">Nhật Không</th>'
        "</tr></thead><tbody><tr>"
        f'<td style="font-weight:600">{_esc(chart["menh_cung"]["display"])}</td>'
        f'<td style="font-weight:600">{_esc(chart["thai_nguyen"]["display"])}</td>'
        f'<td>{_esc(chart["tuan_khong"]["nien_khong"]["display"])}</td>'
        f'<td>{_esc(chart["tuan_khong"]["nhat_khong"]["display"])}</td>'
        "</tr></tbody></table></div></div>"
    )

    return "".join(parts)
