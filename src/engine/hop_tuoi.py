"""
hop_tuoi.py — Hợp Tuổi v2: purpose-based qualitative compatibility.

evaluate_criterion / compute_verdict are pure given person dicts.
load_readings() caches JSON from docs/seed/hop-tuoi-readings.json (first load).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.can_chi import CAN_HANH, CAN_NAMES, CHI_NAMES, is_xung
from engine.cuong_nhuoc import analyze_chart_strength
from engine.dung_than import KHAC_BY, KHAC_TARGET, SINH_BY, SINH_TARGET, find_dung_than
from engine.sao_ngay import LUC_HOP_MAP, TAM_HOP_SETS
from engine.thap_than import KHAC_MAP, get_thap_than

# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

RELATIONSHIP_TYPES: dict[str, dict[str, Any]] = {
    "PHU_THE": {"label": "Phu Thê", "symmetric": True},
    "DOI_TAC": {"label": "Đối Tác", "symmetric": True},
    "SEP_NHAN_VIEN": {"label": "Sếp — Nhân Viên", "symmetric": False},
    "DONG_NGHIEP": {"label": "Đồng Nghiệp", "symmetric": True},
    "BAN_BE": {"label": "Bạn Bè", "symmetric": True},
    "PHU_TU": {"label": "Phụ Tử", "symmetric": False},
    "ANH_CHI_EM": {"label": "Anh Chị Em", "symmetric": True},
    "THAY_TRO": {"label": "Thầy — Trò", "symmetric": False},
}

CRITERIA_BY_RELATIONSHIP: dict[str, list[dict[str, int]]] = {
    "PHU_THE": [
        {"key": "nap_am", "weight": 2},
        {"key": "luc_hop", "weight": 3},
        {"key": "tam_hop", "weight": 2},
        {"key": "dia_chi_xung", "weight": 2},
        {"key": "thien_can", "weight": 1},
        {"key": "nhat_chu", "weight": 1},
        {"key": "thap_than_spouse", "weight": 2},
        {"key": "phu_the_gioi_tinh", "weight": 1},
    ],
    "DOI_TAC": [
        {"key": "nap_am", "weight": 1},
        {"key": "nhat_chu", "weight": 3},
        {"key": "dung_than_bo_tro", "weight": 2},
        {"key": "dia_chi_xung", "weight": 2},
        {"key": "thien_can", "weight": 1},
    ],
    "SEP_NHAN_VIEN": [
        {"key": "nap_am_directed", "weight": 2},
        {"key": "nhat_chu_directed", "weight": 3},
        {"key": "cuong_nhuoc_pair", "weight": 2},
        {"key": "thien_can_directed", "weight": 2},
    ],
    "DONG_NGHIEP": [
        {"key": "nhat_chu", "weight": 2},
        {"key": "dia_chi_xung", "weight": 2},
        {"key": "thien_can", "weight": 2},
        {"key": "nap_am", "weight": 1},
    ],
    "BAN_BE": [
        {"key": "dia_chi_harmony", "weight": 3},
        {"key": "nap_am", "weight": 2},
        {"key": "nhat_chu", "weight": 1},
    ],
    "PHU_TU": [
        {"key": "nap_am_directed", "weight": 3},
        {"key": "dia_chi_xung", "weight": 2},
        {"key": "thien_can_directed", "weight": 2},
    ],
    "ANH_CHI_EM": [
        {"key": "nap_am", "weight": 2},
        {"key": "dia_chi_xung", "weight": 2},
        {"key": "nhat_chu", "weight": 2},
    ],
    "THAY_TRO": [
        {"key": "nhat_chu_directed", "weight": 3},
        {"key": "dung_than_bo_tro", "weight": 2},
        {"key": "cuong_nhuoc_pair", "weight": 2},
    ],
}

CRITERION_LABELS: dict[str, str] = {
    "nap_am": "Ngũ Hành Nạp Âm",
    "nap_am_directed": "Ngũ Hành Nạp Âm (chiều quan hệ)",
    "luc_hop": "Lục Hợp",
    "tam_hop": "Tam Hợp",
    "dia_chi_xung": "Địa Chi",
    "dia_chi_harmony": "Địa Chi (Lục Hợp / Tam Hợp)",
    "thien_can": "Thiên Can",
    "thien_can_directed": "Thiên Can (chiều quan hệ)",
    "nhat_chu": "Nhật Chủ",
    "nhat_chu_directed": "Nhật Chủ (chiều quan hệ)",
    "dung_than_bo_tro": "Dụng Thần bổ trợ",
    "cuong_nhuoc_pair": "Cường Nhược",
    "thap_than_spouse": "Thập Thần (Phu Thê)",
    "phu_the_gioi_tinh": "Giới tính (phu thê)",
}

# Ngũ hành — symmetric sentiment (reuse hop_tuoi route logic)
def _symmetric_hanh_relation(h1: str, h2: str) -> tuple[str, str]:
    """Return (relation_vn, sentiment)."""
    if h1 == h2:
        return ("Tỷ Hòa", "neutral")
    if SINH_BY.get(h1) == h2 or SINH_TARGET.get(h1) == h2:
        return ("Tương Sinh", "positive")
    if KHAC_BY.get(h1) == h2 or KHAC_TARGET.get(h1) == h2:
        return ("Tương Khắc", "negative")
    return ("Bình Hòa", "neutral")


def _p1_sinh_p2(h1: str, h2: str) -> bool:
    return SINH_TARGET.get(h1) == h2


def _p2_khac_p1(h1: str, h2: str) -> bool:
    """h2's element controls h1."""
    return KHAC_MAP.get(h2) == h1


def _directed_nap_am_sentiment(
    h1: str, h2: str, rel: str
) -> tuple[str, str, str]:
    """
    p1 = user (above for SEP/THAY/parent), p2 = other.
    Returns (relation_label, sentiment, prose_hint).
    """
    if h1 == h2:
        return ("Tỷ Hòa", "neutral", "cùng hành, cần đa dạng hóa năng lượng")

    if rel in ("SEP_NHAN_VIEN", "THAY_TRO"):
        if _p1_sinh_p2(h1, h2):
            return ("Tương Sinh", "positive", "phía người hỏi sinh trợ cho đối phương")
        if _p2_khac_p1(h1, h2):
            return ("Tương Khắc", "negative", "đối phương khắc về hành với người hỏi")
        if _p1_sinh_p2(h2, h1):
            return ("Được sinh", "positive", "đối phương sinh trợ cho người hỏi")
        rname, sym = _symmetric_hanh_relation(h1, h2)
        return (rname, sym, "quan hệ hành tương đối cân bằng")

    if rel == "PHU_TU":
        if _p1_sinh_p2(h1, h2):
            return ("Sinh xuất", "positive", "mệnh cha mẹ sinh trợ cho con")
        if _p2_khac_p1(h1, h2):
            return ("Tương Khắc", "negative", "hành con khắc về phía cha mẹ, cần dưỡng sinh")
        if _p1_sinh_p2(h2, h1):
            return ("Được sinh", "neutral", "con sinh trợ cha mẹ — cần ranh giới lành mạnh")
        rname, sym = _symmetric_hanh_relation(h1, h2)
        return (rname, sym, "quan hệ Nạp Âm cần quan sát thêm")

    rname, sym = _symmetric_hanh_relation(h1, h2)
    return (rname, sym, "")


def year_luc_hop(c1: int, c2: int) -> bool:
    return LUC_HOP_MAP.get(c1) == c2


def year_tam_hop(c1: int, c2: int) -> bool:
    s = TAM_HOP_SETS.get(c1)
    return s is not None and c2 in s


def _both_tu_tru(p1: dict, p2: dict) -> tuple[dict | None, dict | None]:
    return (p1.get("tu_tru"), p2.get("tu_tru"))


def evaluate_criterion(
    key: str,
    p1: dict,
    p2: dict,
    relationship_type: str,
) -> dict[str, str]:
    """Return {name, sentiment, description}."""
    name = CRITERION_LABELS.get(key, key)
    h1, h2 = p1["hanh"], p2["hanh"]
    y1, y2 = p1["year_chi_idx"], p2["year_chi_idx"]
    dc1, dc2 = p1["day_can_idx"], p2["day_can_idx"]

    if key == "nap_am":
        rel, sent = _symmetric_hanh_relation(h1, h2)
        desc = f"{p1['hanh']} và {p2['hanh']} — {rel} (Nạp Âm năm)."
        return {"name": name, "sentiment": sent, "description": desc}

    if key == "nap_am_directed":
        rel, sent, hint = _directed_nap_am_sentiment(h1, h2, relationship_type)
        desc = f"{p1['hanh']} ↔ {p2['hanh']}: {rel}. {hint}.".strip()
        return {"name": name, "sentiment": sent, "description": desc}

    if key == "luc_hop":
        ok = year_luc_hop(y1, y2)
        n1, n2 = CHI_NAMES[y1], CHI_NAMES[y2]
        if ok:
            return {
                "name": name,
                "sentiment": "positive",
                "description": f"{n1} và {n2} là cặp Lục Hợp — thuận duyên và hòa khí.",
            }
        return {
            "name": name,
            "sentiment": "neutral",
            "description": f"{n1} và {n2} không thuộc Lục Hợp — không xấu tự thân.",
        }

    if key == "tam_hop":
        ok = year_tam_hop(y1, y2)
        n1, n2 = CHI_NAMES[y1], CHI_NAMES[y2]
        if ok:
            return {
                "name": name,
                "sentiment": "positive",
                "description": f"{n1} và {n2} đồng cục Tam Hợp — nền tảng tương trợ.",
            }
        return {
            "name": name,
            "sentiment": "neutral",
            "description": f"{n1} và {n2} không cùng Tam Hợp.",
        }

    if key == "dia_chi_xung":
        x = is_xung(y1, y2)
        n1, n2 = CHI_NAMES[y1], CHI_NAMES[y2]
        if x:
            return {
                "name": name,
                "sentiment": "negative",
                "description": f"{n1} và {n2} tương xung — dễ căng thẳng, nên hóa giải bằng phong thủy và giao tiếp.",
            }
        return {
            "name": name,
            "sentiment": "neutral",
            "description": f"{n1} và {n2} không tương xung trực tiếp — trung tính về Chi năm.",
        }

    if key == "dia_chi_harmony":
        if is_xung(y1, y2):
            out = evaluate_criterion("dia_chi_xung", p1, p2, relationship_type)
        elif year_luc_hop(y1, y2):
            out = evaluate_criterion("luc_hop", p1, p2, relationship_type)
        elif year_tam_hop(y1, y2):
            out = evaluate_criterion("tam_hop", p1, p2, relationship_type)
        else:
            n1, n2 = CHI_NAMES[y1], CHI_NAMES[y2]
            out = {
                "name": name,
                "sentiment": "neutral",
                "description": f"{n1} và {n2} không xung, không Lục/Tam Hợp đặc biệt — trung tính.",
            }
        # Giữ nhãn tiêu chí gốc (Bạn bè) thay vì tên tiêu chí con
        out = {**out, "name": name}
        return out

    if key == "thien_can":
        rel, sent = _symmetric_hanh_relation(CAN_HANH[dc1], CAN_HANH[dc2])
        c1n, c2n = CAN_NAMES[dc1], CAN_NAMES[dc2]
        desc = f"Can ngày {c1n} và {c2n} — {rel}."
        return {"name": name, "sentiment": sent, "description": desc}

    if key == "thien_can_directed":
        # p1 "trên" — sinh/khắc từ góc p1
        e1, e2 = CAN_HANH[dc1], CAN_HANH[dc2]
        if _p1_sinh_p2(e1, e2):
            sent, desc = "positive", f"{CAN_NAMES[dc1]} sinh trợ {CAN_NAMES[dc2]} — thuận chiều quyền uy."
        elif _p2_khac_p1(e1, e2):
            sent, desc = "negative", f"{CAN_NAMES[dc2]} khắc về phía {CAN_NAMES[dc1]} — dễ mất cân bằng quyền lực."
        else:
            rel, sent = _symmetric_hanh_relation(e1, e2)
            desc = f"{CAN_NAMES[dc1]} và {CAN_NAMES[dc2]} — {rel}."
        return {"name": name, "sentiment": sent, "description": desc}

    if key == "nhat_chu":
        rel, sent = _symmetric_hanh_relation(p1["nhat_chu_hanh"], p2["nhat_chu_hanh"])
        desc = f"Nhật Chủ {p1['nhat_chu_hanh']} và {p2['nhat_chu_hanh']} — {rel}."
        return {"name": name, "sentiment": sent, "description": desc}

    if key == "nhat_chu_directed":
        nh1, nh2 = p1["nhat_chu_hanh"], p2["nhat_chu_hanh"]
        if relationship_type == "THAY_TRO":
            # thầy (p1) sinh trò = tốt
            if _p1_sinh_p2(nh1, nh2):
                return {
                    "name": name,
                    "sentiment": "positive",
                    "description": "Hành Nhật Chủ người hỏi sinh trợ người kia — thuận vai trò dạy dỗ.",
                }
            if _p2_khac_p1(nh1, nh2):
                return {
                    "name": name,
                    "sentiment": "negative",
                    "description": "Hành đối phương khắc về Nhật Chủ người hỏi — cần kiên nhẫn.",
                }
        if relationship_type == "SEP_NHAN_VIEN":
            if _p1_sinh_p2(nh1, nh2):
                return {
                    "name": name,
                    "sentiment": "positive",
                    "description": "Sếp (người hỏi) sinh trợ nhân viên — dễ phát triển năng lực.",
                }
            if _p2_khac_p1(nh1, nh2):
                return {
                    "name": name,
                    "sentiment": "negative",
                    "description": "Nhân viên khắc về phía sếp — dễ bất đồng, cần ranh giới rõ.",
                }
        rel, sent = _symmetric_hanh_relation(nh1, nh2)
        return {
            "name": name,
            "sentiment": sent,
            "description": f"{nh1} và {nh2} — {rel}.",
        }

    if key == "dung_than_bo_tro":
        t1, t2 = _both_tu_tru(p1, p2)
        if t1 is None or t2 is None:
            return {
                "name": name,
                "sentiment": "neutral",
                "description": "Cần giờ sinh đầy đủ để xét Dụng Thần bổ trợ sâu.",
            }
        d1 = find_dung_than(t1)
        d2 = find_dung_than(t2)
        dt1, dt2 = d1["dung_than"], d2["dung_than"]
        h1t, h2t = d1["hi_than"], d2["hi_than"]

        def _helps(target: dict, other: dict) -> bool:
            """other's Nạp Âm / Nhật Chủ có bổ trợ Dụng Thần hoặc Hỷ Thần của target."""
            dt, ht = target["dung_than"], target["hi_than"]
            oh = other["nhat_chu_hanh"]
            om = other["hanh"]
            return oh == dt or om == dt or oh == ht or om == ht

        if _helps(d1, p2):
            return {
                "name": name,
                "sentiment": "positive",
                "description": (
                    f"Đối phương bổ trợ Dụng/Hỷ Thần "
                    f"({dt1}, {h1t}) của người hỏi."
                ),
            }
        if _helps(d2, p1):
            return {
                "name": name,
                "sentiment": "positive",
                "description": (
                    f"Người hỏi bổ trợ Dụng/Hỷ Thần "
                    f"({dt2}, {h2t}) của đối phương."
                ),
            }
        if (
            d1["ky_than"] in (p2["nhat_chu_hanh"], p2["hanh"])
            or d2["ky_than"] in (p1["nhat_chu_hanh"], p1["hanh"])
        ):
            return {
                "name": name,
                "sentiment": "negative",
                "description": "Một bên chạm Kỵ Thần của bên kia — dễ hao tổn.",
            }
        return {
            "name": name,
            "sentiment": "neutral",
            "description": "Dụng Thần hai bên không xung đột rõ, cần thêm ngữ cảnh.",
        }

    if key == "cuong_nhuoc_pair":
        t1, t2 = _both_tu_tru(p1, p2)
        if t1 is None or t2 is None:
            return {
                "name": name,
                "sentiment": "neutral",
                "description": "Cần giờ sinh để xét Cường Nhược.",
            }
        s1 = analyze_chart_strength(t1)["strength"]
        s2 = analyze_chart_strength(t2)["strength"]
        if s1 != s2 and ("nhược" in (s1, s2) and "vượng" in (s1, s2)):
            return {
                "name": name,
                "sentiment": "positive",
                "description": "Một bên vượng một bên nhược — có thể bổ sung vai trò.",
            }
        if s1 == s2 == "vượng":
            return {
                "name": name,
                "sentiment": "negative",
                "description": "Hai lá số đều vượng — dễ tranh chấp, cần chia sẻ quyền lực.",
            }
        return {
            "name": name,
            "sentiment": "neutral",
            "description": f"Cường Nhược: {s1} / {s2} — tương đối cân bằng.",
        }

    if key == "thap_than_spouse":
        t1, t2 = _both_tu_tru(p1, p2)
        if t1 is None or t2 is None:
            return {
                "name": name,
                "sentiment": "neutral",
                "description": "Cần giờ sinh để xét Thập Thần phu thê (Nhật Chủ).",
            }
        dm1 = t1["day"]["can_idx"]
        dm2 = t2["day"]["can_idx"]
        g = get_thap_than(dm1, dm2)
        sent = "positive" if g["category"] == "thuận lợi" else "neutral"
        if g["key"] in ("that_sat", "kiep_tai", "thuong_quan"):
            sent = "negative"
        desc = (
            f"Quan hệ Thập Thần giữa hai Nhật Chủ: {g['name']} "
            f"({g['category']})."
        )
        return {"name": name, "sentiment": sent, "description": desc}

    if key == "phu_the_gioi_tinh":
        if relationship_type != "PHU_THE":
            return {
                "name": name,
                "sentiment": "neutral",
                "description": "Tiêu chí chỉ dùng cho phu thê.",
            }
        g1, g2 = p1.get("gender"), p2.get("gender")
        if g1 is None or g2 is None:
            return {
                "name": name,
                "sentiment": "neutral",
                "description": (
                    "Chưa có đủ giới tính hai phía — không áp tiêu chí nam/nữ "
                    "trong luận phu thê."
                ),
            }
        if g1 != g2:
            return {
                "name": name,
                "sentiment": "positive",
                "description": (
                    "Hai phía khác giới theo dữ liệu — truyền thống luận phu thê "
                    "thường căn cứ cặp nam/nữ."
                ),
            }
        return {
            "name": name,
            "sentiment": "neutral",
            "description": (
                "Hai phía cùng mã giới trong dữ liệu — không dùng tiêu chí nam/nữ "
                "cổ điển làm chuẩn xấu hay tốt."
            ),
        }

    return {"name": name, "sentiment": "neutral", "description": "Chưa cấu hình tiêu chí."}


def sentiment_score(s: str) -> int:
    return {"positive": 1, "neutral": 0, "negative": -1}.get(s, 0)


def compute_verdict(
    criteria_results: list[dict[str, Any]],
    weights: list[int],
) -> tuple[str, int]:
    """Weighted average → verdict label + level 1..4."""
    if len(criteria_results) != len(weights):
        raise ValueError("criteria_results và weights phải cùng độ dài")

    wsum = sum(weights) or 1
    acc = sum(
        sentiment_score(r["sentiment"]) * w for r, w in zip(criteria_results, weights)
    )
    avg = acc / wsum

    if avg >= 0.5:
        level = 1
    elif avg >= 0.1:
        level = 2
    elif avg >= -0.3:
        level = 3
    else:
        level = 4

    verdicts = {
        1: "Rất tương hợp",
        2: "Tương hợp",
        3: "Cần lưu ý",
        4: "Nhiều thử thách",
    }
    return verdicts[level], level


_READINGS_CACHE: dict[str, Any] | None = None


def _readings_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent.parent
        / "docs"
        / "seed"
        / "hop-tuoi-readings.json"
    )


def load_readings() -> dict[str, Any]:
    global _READINGS_CACHE
    if _READINGS_CACHE is None:
        p = _readings_path()
        with open(p, encoding="utf-8") as f:
            _READINGS_CACHE = json.load(f)
    return _READINGS_CACHE


def _verdict_key(level: int) -> str:
    return {1: "rat_tuong_hop", 2: "tuong_hop", 3: "can_luu_y", 4: "nhieu_thu_thach"}[level]


def build_reading_and_advice(
    relationship_type: str,
    level: int,
    criteria_results: list[dict[str, str]],
) -> tuple[str, str]:
    data = load_readings()
    rel = data.get(relationship_type, {})
    vk = _verdict_key(level)
    template_r = rel.get("reading", {}).get(vk, "")
    template_a = rel.get("advice", {}).get(vk, "")

    # Placeholders: first sentences from criteria
    ctx = " ".join(c["description"] for c in criteria_results[:3])
    neg = next((c["description"] for c in criteria_results if c["sentiment"] == "negative"), "")

    # Tránh str.format: mô tả tiêu chí có thể chứa "{" / "}" trong tương lai
    def _fill(tpl: str) -> str:
        return tpl.replace("{hints}", ctx).replace("{neg_hint}", neg or ctx)

    reading = _fill(template_r)
    advice = _fill(template_a)
    return reading, advice


def analyze_compatibility(
    p1: dict,
    p2: dict,
    relationship_type: str,
) -> dict[str, Any]:
    """Main entry — p1,p2 are internal dicts with year_chi_idx, hanh, tu_tru optional, etc."""
    if relationship_type not in RELATIONSHIP_TYPES:
        raise ValueError(f"relationship_type không hợp lệ: {relationship_type}")

    specs = CRITERIA_BY_RELATIONSHIP[relationship_type]
    weights = [s["weight"] for s in specs]
    criteria_results: list[dict[str, str]] = []
    for s in specs:
        row = evaluate_criterion(s["key"], p1, p2, relationship_type)
        criteria_results.append(row)

    verdict, level = compute_verdict(criteria_results, weights)
    reading, advice = build_reading_and_advice(relationship_type, level, criteria_results)

    meta = RELATIONSHIP_TYPES[relationship_type]
    return {
        "relationship_type": relationship_type,
        "relationship_label": meta["label"],
        "verdict": verdict,
        "verdict_level": level,
        "criteria": criteria_results,
        "reading": reading,
        "advice": advice,
    }


def _validate_registry() -> None:
    """Đảm bảo registry nhất quán: keys khớp; quan hệ đối xứng không dùng *_directed."""
    rt = set(RELATIONSHIP_TYPES)
    cr = set(CRITERIA_BY_RELATIONSHIP)
    if rt != cr:
        raise RuntimeError(
            "RELATIONSHIP_TYPES và CRITERIA_BY_RELATIONSHIP không khớp: "
            f"{sorted(rt ^ cr)}"
        )
    for code, meta in RELATIONSHIP_TYPES.items():
        keys = [s["key"] for s in CRITERIA_BY_RELATIONSHIP[code]]
        if meta["symmetric"]:
            bad = [k for k in keys if k.endswith("_directed")]
            if bad:
                raise RuntimeError(
                    f"{code} là quan hệ đối xứng nhưng có tiêu chí chiều: {bad}"
                )
        else:
            if not any(k.endswith("_directed") for k in keys):
                raise RuntimeError(
                    f"{code} là quan hệ có chiều nhưng thiếu tiêu chí *_directed"
                )


_validate_registry()
