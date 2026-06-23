"""
menh_ban_html.py — Self-contained HTML fragment for Mệnh Bàn Tứ Trụ.

Renders the same layout as web/components/MenhBanTuTru.tsx using inline CSS
for CMS/article embed (no React/Tailwind). The chart is a single continuous
"tờ lá số" sheet: one bordered frame, a fixed vermilion label column on the
left, and content rows that each divide into their own equal-width columns.

Source: docs/algorithm.md §22.11
"""

from __future__ import annotations

import html
import re
from typing import Any

_PILLAR_KEYS = ("year", "month", "day", "hour")
_THAN_SAT_HEADERS = ("Niên Thần", "Nguyệt Thần", "Nhật Thần", "Thời Thần")
_MENH_HEADERS = ("Mệnh Cung", "Thai Nguyên", "Niên Không", "Nhật Không")

_HANH_COLOR: dict[str, str] = {
    "Mộc": "#2f6f4f",
    "Hỏa": "#a3201f",
    "Thổ": "#9a7c22",
    "Kim": "#6f6a52",
    "Thủy": "#274b6d",
}

_MBTT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
.mbtt{--paper:#f0ece2;--paper-warm:#ede7d3;--ink:#18150e;--muted:#7a7050;
--gold:#c5a55a;--gold-deep:#9a7c22;--vermilion:#a3201f;--jade:#5e7d5e;
--hairline:rgba(154,124,34,0.30);--gold-hl:rgba(197,165,90,0.30);
font-family:"Open Sans",system-ui,sans-serif;color:var(--ink);max-width:56rem;
margin:0 auto;overflow-x:auto}
.mbtt *{box-sizing:border-box}
.mbtt-sheet{min-width:760px;background:var(--paper);border:1px solid var(--gold);
border-radius:6px;box-shadow:0 4px 14px rgba(14,28,20,0.10);overflow:hidden}
.mbtt-head{display:flex;flex-direction:column;gap:1rem;padding:1.25rem}
@media(min-width:768px){.mbtt-head{flex-direction:row;align-items:flex-start;
justify-content:space-between}}
.mbtt-brand{font-family:"Open Sans",system-ui,sans-serif;font-size:11px;
letter-spacing:0.3em;text-transform:uppercase;color:var(--gold-deep);margin:0}
.mbtt-title{font-family:"Open Sans",system-ui,sans-serif;font-size:1.75rem;
font-weight:700;letter-spacing:0.05em;color:var(--vermilion);margin:0.25rem 0 0}
.mbtt-name{font-size:1.125rem;font-weight:600;margin:0.5rem 0 0}
.mbtt-meta{display:grid;grid-template-columns:auto 1fr;gap:0.35rem 0.75rem;
font-size:0.875rem;margin:0}
.mbtt-meta dt{font-family:"Open Sans",system-ui,sans-serif;text-transform:uppercase;
letter-spacing:0.05em;color:var(--muted);margin:0}
.mbtt-meta dd{margin:0}
.mbtt-khoi{font-weight:600;color:var(--vermilion)}
.mbtt-row{display:flex;border-top:1px solid var(--hairline)}
.mbtt-label{width:6rem;flex-shrink:0;display:flex;align-items:center;
border-right:1px solid var(--hairline);background:var(--paper-warm);padding:0.5rem;
font-family:"Open Sans",system-ui,sans-serif;font-size:11px;font-weight:600;
text-transform:uppercase;letter-spacing:0.04em;line-height:1.15;color:var(--vermilion)}
.mbtt-content{flex:1;min-width:0;display:flex;flex-direction:column}
.mbtt-cols{display:grid;flex:1 1 auto}
.mbtt-cols--sub{border-top:1px solid var(--hairline)}
.mbtt-cell{border-right:1px solid var(--hairline);padding:0.5rem;text-align:center;
vertical-align:middle}
.mbtt-cell:last-child{border-right:0}
.mbtt-sm{font-size:0.875rem}
.mbtt-xs{font-size:0.75rem}
.mbtt-strong{font-weight:600}
.mbtt-pillar{background:rgba(237,231,211,0.6);padding-top:0.75rem;padding-bottom:0.75rem}
.mbtt-can{font-family:"Open Sans",system-ui,sans-serif;font-size:1.75rem;
font-weight:700;line-height:1.2}
.mbtt-disp{font-family:"Open Sans",system-ui,sans-serif;font-weight:600;line-height:1.15}
.mbtt-nhat{font-family:"Open Sans",system-ui,sans-serif;font-weight:700;
text-transform:uppercase;color:var(--vermilion)}
.mbtt-subhead{background:var(--paper-warm);font-family:"Open Sans",system-ui,sans-serif;
font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;
color:var(--jade)}
.mbtt-age{color:var(--vermilion)}
.mbtt-muted{color:var(--muted)}
.mbtt-hl{background:var(--gold-hl)}
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


def _birth_hour_display(header: dict[str, Any]) -> str:
    """Short zodiac hour label for the Năm sinh dương row (e.g. Giờ Mão, Giờ Tý Sớm)."""
    label = header.get("birth_time_label")
    if label:
        return str(label).split(" (", 1)[0]
    disp = str(header.get("duong_lich_display", ""))
    time_match = re.search(r"-\s*(\d{1,2}:\d{2})", disp)
    return time_match.group(1) if time_match else ""


def _birth_cells(header: dict[str, Any]) -> list[str]:
    """[năm, tháng, ngày, giờ] for the Năm sinh dương row."""
    iso = str(header.get("duong_lich", ""))
    date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso)
    hour = _birth_hour_display(header)
    if not date_match:
        return ["", "", "", hour]
    y, m, d = date_match.groups()
    return [str(int(y)), str(int(m)), str(int(d)), hour]


def _hanh_span(text: str, hanh: str, *, large: bool = False) -> str:
    color = _HANH_COLOR.get(hanh, "var(--ink)")
    size = "1.75rem" if large else "inherit"
    family = "'Open Sans',system-ui,sans-serif" if large else "inherit"
    weight = "700" if large else "600"
    return (
        f'<span style="color:{color};font-size:{size};'
        f'font-family:{family};font-weight:{weight}">{_esc(text)}</span>'
    )


def _row(label: str, content: str) -> str:
    return (
        f'<div class="mbtt-row"><div class="mbtt-label">{_esc(label)}</div>'
        f'<div class="mbtt-content">{content}</div></div>'
    )


def _cols(n: int, cells: str, *, sub: bool = False) -> str:
    cls = "mbtt-cols mbtt-cols--sub" if sub else "mbtt-cols"
    return (
        f'<div class="{cls}" '
        f'style="grid-template-columns:repeat({n},minmax(0,1fr))">{cells}</div>'
    )


def _cell(inner: str, *, cls: str = "") -> str:
    klass = f"mbtt-cell {cls}".strip()
    return f'<div class="{klass}">{inner}</div>'


def render_menh_ban_html(chart: dict[str, Any]) -> str:
    """Return an embeddable HTML fragment (with scoped <style>) for a menh_ban payload."""
    h = chart["header"]
    pillars = chart["pillars"]

    parts: list[str] = [
        '<div class="mbtt">',
        f"<style>{_MBTT_CSS}</style>",
        '<div class="mbtt-sheet">',
        # Header band
        '<div class="mbtt-head"><div>',
        '<p class="mbtt-brand">Luận Giải Bát Tự</p>',
        '<h2 class="mbtt-title">Mệnh Bàn Tứ Trụ</h2>',
        f'<p class="mbtt-name">{_esc(h.get("name") or "—")}</p>',
        "</div>",
        '<dl class="mbtt-meta">',
        f"<dt>Giới tính</dt><dd>{_esc(h.get('gender_label', ''))}</dd>",
        f"<dt>Dương lịch</dt><dd>{_esc(h.get('duong_lich_display', ''))}</dd>",
        f"<dt>Âm lịch</dt><dd>{_esc(h['am_lich']['display'])}</dd>",
        f"<dt>Tiết khí</dt><dd>{_esc(h['tiet_khi']['name'])} "
        f"(nguyệt lệnh {_esc(h.get('nguyet_lenh', ''))})</dd>",
        f'<dt>Khởi vận</dt><dd class="mbtt-khoi">'
        f"{_esc(_format_dmy(h['khoi_van_date']))}</dd>",
        "</dl></div>",
    ]

    # Năm sinh dương
    birth = _birth_cells(h)
    parts.append(
        _row(
            "Năm sinh dương",
            _cols(
                4,
                "".join(
                    _cell(_esc(v or "—"), cls="mbtt-sm mbtt-strong") for v in birth
                ),
            ),
        )
    )

    # Thập Thần
    cells = []
    for pk in _PILLAR_KEYS:
        label = pillars[pk]["thap_than"]["short_label"]
        if pk == "day":
            cells.append(_cell(f'<span class="mbtt-nhat">{_esc(label)}</span>', cls="mbtt-sm"))
        else:
            cells.append(_cell(_esc(label), cls="mbtt-sm"))
    parts.append(_row("Thập Thần", _cols(4, "".join(cells))))

    # Bát Tự
    cells = []
    for pk in _PILLAR_KEYS:
        p = pillars[pk]
        inner = (
            '<div class="mbtt-can">'
            f'{_hanh_span(p["can"]["name"], p["can"]["hanh"], large=True)}<br>'
            f'{_hanh_span(p["chi"]["name"], p["chi"]["hanh"], large=True)}</div>'
        )
        cells.append(_cell(inner, cls="mbtt-pillar"))
    parts.append(_row("Bát Tự", _cols(4, "".join(cells))))

    # Nạp Âm
    parts.append(
        _row(
            "Nạp Âm Ngũ Hành",
            _cols(
                4,
                "".join(
                    _cell(_esc(pillars[pk]["nap_am"]["name"]), cls="mbtt-sm")
                    for pk in _PILLAR_KEYS
                ),
            ),
        )
    )

    # Can Chi Tàng Ẩn
    cells = []
    for pk in _PILLAR_KEYS:
        spans = " ".join(
            _hanh_span(t["can_name"], t["hanh"]) for t in pillars[pk]["tang_can"]
        )
        cells.append(_cell(spans, cls="mbtt-sm"))
    parts.append(_row("Can Chi Tàng Ẩn", _cols(4, "".join(cells))))

    # Phó Tinh
    parts.append(
        _row(
            "Phó Tinh",
            _cols(
                4,
                "".join(
                    _cell(
                        _esc("  ".join(p["short_label"] for p in pillars[pk]["pho_tinh"])),
                        cls="mbtt-sm",
                    )
                    for pk in _PILLAR_KEYS
                ),
            ),
        )
    )

    # Thập Nhị Thần
    parts.append(
        _row(
            "Thập Nhị Thần",
            _cols(
                4,
                "".join(
                    _cell(_esc(pillars[pk]["truong_sinh"]["label_vi"]), cls="mbtt-sm")
                    for pk in _PILLAR_KEYS
                ),
            ),
        )
    )

    # Đại Vận
    cycles = chart["dai_van"]["cycles"]
    n_dv = len(cycles)
    dv_cells = []
    for c in cycles:
        can, _, chi = c["display"].partition(" ")
        dv_cells.append(
            _cell(f'<div class="mbtt-disp">{_esc(can)}<br>{_esc(chi)}</div>', cls="mbtt-sm")
        )
    parts.append(_row("Đại Vận", _cols(n_dv, "".join(dv_cells))))
    dv_year_cells = []
    for c in cycles:
        dv_year_cells.append(
            _cell(
                f'<div class="mbtt-age">{_esc(c["age_label"])}</div>'
                f'<div class="mbtt-muted">{_esc(c["start_year"])}</div>',
                cls="mbtt-xs",
            )
        )
    parts.append(_row("Năm", _cols(n_dv, "".join(dv_year_cells))))

    # Lưu Niên
    luu = chart["luu_nien"]
    n_ln = len(luu)
    ln_cells = []
    for row in luu:
        hl = "mbtt-hl " if row.get("selected") else ""
        can, _, chi = row["display"].partition(" ")
        ln_cells.append(
            _cell(
                f'<div class="mbtt-disp">{_esc(can)}<br>{_esc(chi)}</div>',
                cls=f"{hl}mbtt-sm",
            )
        )
    parts.append(_row("Lưu Niên", _cols(n_ln, "".join(ln_cells))))
    ln_year_cells = []
    for row in luu:
        hl = "mbtt-hl " if row.get("selected") else ""
        ln_year_cells.append(
            _cell(
                f'<div class="mbtt-age">{_esc(row["year"])}</div>'
                f'<div class="mbtt-muted">{_esc(row["age_label"])}</div>',
                cls=f"{hl}mbtt-xs",
            )
        )
    parts.append(_row("Năm", _cols(n_ln, "".join(ln_year_cells))))

    # Thần Sát Nguyên Cục
    head = "".join(_cell(_esc(label), cls="mbtt-subhead") for label in _THAN_SAT_HEADERS)
    data_cells = []
    for pk in _PILLAR_KEYS:
        stars = pillars[pk]["than_sat"]
        if stars:
            inner = (
                '<div class="mbtt-stars">'
                + "".join(f"<span>{_esc(s['name'])}</span>" for s in stars)
                + "</div>"
            )
            data_cells.append(_cell(inner, cls="mbtt-sm"))
        else:
            data_cells.append(_cell('<span class="mbtt-muted">—</span>', cls="mbtt-sm"))
    parts.append(
        _row(
            "Thần Sát Nguyên Cục",
            _cols(4, head) + _cols(4, "".join(data_cells), sub=True),
        )
    )

    # Mệnh
    head = "".join(_cell(_esc(label), cls="mbtt-subhead") for label in _MENH_HEADERS)
    menh_cells = (
        _cell(_esc(chart["menh_cung"]["display"]), cls="mbtt-sm mbtt-strong")
        + _cell(_esc(chart["thai_nguyen"]["display"]), cls="mbtt-sm mbtt-strong")
        + _cell(_esc(chart["tuan_khong"]["nien_khong"]["display"]), cls="mbtt-sm")
        + _cell(_esc(chart["tuan_khong"]["nhat_khong"]["display"]), cls="mbtt-sm")
    )
    parts.append(
        _row("Mệnh", _cols(4, head) + _cols(4, menh_cells, sub=True))
    )

    parts.append("</div></div>")
    return "".join(parts)
