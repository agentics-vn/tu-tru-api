"""
scoring.py — Layer 3: Intent-aware scoring engine.

Ported from scoring.js.
Source of truth: docs/algorithm.md §10.

Special Rules:
  1. Nguyệt Đức ngoại lệ cho KIEN_TUNG
  2. Thiên Xá nghịch lý (bonus for tế tự, penalty for động thổ)
  3. Tháng Cô Hồn (handled upstream in filter.py)
"""

from __future__ import annotations

from engine.sao_ngay import (
    check_dai_hao,
    check_dich_ma,
    check_giai_than,
    check_nguyet_sat,
    check_sat_chu,
    check_thien_an,
    check_thien_cuong,
    check_thien_nguc_thien_hoa,
    check_thien_phuc,
    check_thien_tac,
    check_tho_tu,
)

# ─────────────────────────────────────────────────────────────────────────────
# SPECIAL RULE 2 LOOKUP TABLES
# ─────────────────────────────────────────────────────────────────────────────

THIEN_XA_BONUS_INTENTS: frozenset[str] = frozenset({
    "TE_TU", "GIAI_HAN", "AN_TANG", "CAI_TANG",
    "CAU_TU", "KIEN_TUNG", "KHAM_BENH",
})

THIEN_XA_PENALTY_INTENTS: frozenset[str] = frozenset({
    "DONG_THO", "NHAP_TRACH", "LAM_NHA", "DAO_GIENG", "XAY_BEP",
})

# ─────────────────────────────────────────────────────────────────────────────
# SCORING CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

BASE_SCORE = 50
TRUC_SCORE_MULTIPLIER = 10

BONUS = {
    "thien_duc": 15,
    "thien_duc_hop": 10,
    "nguyet_duc": 12,
    "nguyet_duc_hop": 8,
    "duong_than_match": 12,
    "intent_bonus": 8,
    "thien_xa_bonus": 8,
    "truc_preferred": 15,
    # Tứ Trụ bonuses (Phase 3-5)
    "dung_than_match": 15,
    "hi_than_match": 8,
    "thap_than_intent": 6,
    "dai_van_favorable": 5,
}

PENALTY = {
    "can_khac": -8,
    "ky_than_match": -10,
    "intent_penalty": -15,
    "thien_xa_penalty": -15,
    "truc_forbidden": -20,
    "layer2_severity2": -5,
    # Tứ Trụ penalties (Phase 3-5)
    "ky_than_v2_match": -12,
    "cuu_than_match": -8,
    "dai_van_unfavorable": -5,
}

GRADE_THRESHOLDS = {"A": 80, "B": 65, "C": 50}

# ─────────────────────────────────────────────────────────────────────────────
# SAO DETECTORS — maps sao key → check function(day_info, user_chart) → bool
# ─────────────────────────────────────────────────────────────────────────────

SAO_DETECTORS: dict[str, callable] = {
    # Pre-computed in day_info
    "thienDuc": lambda d, u=None: d.get("has_thien_duc", False),
    "thienDucHop": lambda d, u=None: d.get("has_thien_duc_hop", False),
    "nguyetDuc": lambda d, u=None: d.get("has_nguyet_duc", False),
    "nguyetDucHop": lambda d, u=None: d.get("has_nguyet_duc_hop", False),
    "duongThanMatch": lambda d, u: d.get("day_nap_am_hanh") == (u or {}).get("duong_than"),
    "tamNuong": lambda d, u=None: d.get("is_tam_nuong", False),
    "nguyetKy": lambda d, u=None: d.get("is_nguyet_ky", False),
    "duongCongKy": lambda d, u=None: d.get("is_duong_cong_ky", False),
    "thienXa": lambda d, u=None: d.get("has_thien_xa", False),
    # Computed on-the-fly from day_info fields — _sme_verified = False
    "thoTu": lambda d, u=None: check_tho_tu(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
    "giaiThan": lambda d, u=None: check_giai_than(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
    "thienAn": lambda d, u=None: check_thien_an(d.get("day_can_idx", -1), d.get("day_chi_idx", -1)),
    "thienPhuc": lambda d, u=None: check_thien_phuc(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
    "dichMa": lambda d, u=None: check_dich_ma(d.get("day_chi_idx", -1), (u or {}).get("year_chi_idx", -1)),
    "nguyetSat": lambda d, u=None: check_nguyet_sat(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
    "thienCuong": lambda d, u=None: check_thien_cuong(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
    "daiHao": lambda d, u=None: check_dai_hao(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
    "satChu": lambda d, u=None: check_sat_chu(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
    "thienTac": lambda d, u=None: check_thien_tac(d.get("lunar_month", 0), d.get("day_can_idx", -1)),
    "thienNgucThienHoa": lambda d, u=None: check_thien_nguc_thien_hoa(d.get("lunar_month", 0), d.get("day_chi_idx", -1)),
}

# ─────────────────────────────────────────────────────────────────────────────
# SAO LABELS
# ─────────────────────────────────────────────────────────────────────────────

SAO_LABELS: dict[str, str] = {
    "thienDuc": "Thiên Đức", "thienDucHop": "Thiên Đức Hợp",
    "nguyetDuc": "Nguyệt Đức", "nguyetDucHop": "Nguyệt Đức Hợp",
    "thienXa": "Thiên Xá", "sinhKhi": "Sinh Khí",
    "thienHy": "Thiên Hỷ", "thienPhu": "Thiên Phú",
    "thienTai": "Thiên Tài", "diaTai": "Địa Tài",
    "nguyetTai": "Nguyệt Tài", "locKho": "Lộc Khố",
    "thienMa": "Thiên Mã", "dichMa": "Dịch Mã",
    "phoHo": "Phổ Hộ", "ichHau": "Ích Hậu",
    "tamNuong": "Tam Nương", "nguyetKy": "Nguyệt Kỵ",
    "duongCongKy": "Dương Công Kỵ",
    "thienTac": "Thiên Tặc", "diaTac": "Địa Tặc",
    "thienCuong": "Thiên Cương", "daiHao": "Đại Hao",
    "tieuHao": "Tiểu Hao", "nguyetSat": "Nguyệt Sát",
    "nguyetHoa": "Nguyệt Hỏa", "vatVong": "Vãng Vong",
    "cuuKhong": "Cửu Không", "lucBatThanh": "Lục Bất Thành",
    "nhanCach": "Nhân Cách", "phiMaSat": "Phi Ma Sát",
    "catKhanh": "Cát Khánh", "thienPhuc": "Thiên Phúc",
    "thienQuy": "Thiên Quý", "giaiThan": "Giải Thần",
    "tucThe": "Tục Thế", "yeuYen": "Yếu Yên",
    "thoTu": "Thọ Tử", "thienAn": "Thiên Ân",
    "satChu": "Sát Chủ", "thienNgucThienHoa": "Thiên Ngục/Thiên Hỏa",
}

INTENT_LABELS: dict[str, str] = {
    "KHAI_TRUONG": "Khai trương", "KY_HOP_DONG": "Ký kết hợp đồng",
    "AN_HOI": "Lễ ăn hỏi", "DAM_CUOI": "Đám cưới",
    "DONG_THO": "Động thổ", "NHAP_TRACH": "Nhập trạch",
    "LAM_NHA": "Làm nhà", "AN_TANG": "An táng",
    "CAI_TANG": "Cải táng", "XUAT_HANH": "Xuất hành",
    "CAU_TAI": "Cầu tài lộc", "TE_TU": "Tế tự",
    "KHAM_BENH": "Khám bệnh", "PHAU_THUAT": "Phẫu thuật",
    "NHAP_HOC_THI_CU": "Nhập học / Thi cử", "NHAM_CHUC": "Nhậm chức",
    "MUA_NHA_DAT": "Mua nhà đất", "DAO_GIENG": "Đào giếng",
    "TRONG_CAY": "Trồng cây", "CAU_TU": "Cầu tự",
    "XAY_BEP": "Xây bếp", "LAM_GIUONG": "Làm giường",
    "KIEN_TUNG": "Kiện tụng", "DI_CHUYEN_NGOAI": "Xuất ngoại",
    "GIAI_HAN": "Giải hạn", "MAC_DINH": "Sự kiện chung",
}


def _intent_label(intent: str) -> str:
    return INTENT_LABELS.get(intent, intent)


def _sao_label(key: str) -> str:
    return SAO_LABELS.get(key, key)


def _nguyet_duc_bonus_applies(intent: str) -> bool:
    """SPECIAL RULE 1: Nguyệt Đức excluded from KIEN_TUNG."""
    return intent != "KIEN_TUNG"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCORING FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def compute_score(
    day_info: dict,
    user_chart: dict,
    intent: str,
    intent_rule: dict,
    filter_result: dict,
) -> dict:
    """
    Compute auspiciousness score for a day.

    Returns:
        dict with keys: score, grade, bonus_sao, penalty_sao, reasons_vi
    """
    score = BASE_SCORE
    bonus_sao: list[str] = []
    penalty_sao: list[str] = []
    reasons: list[str] = []

    # 1. Trực score (generic)
    truc_delta = day_info["truc_score"] * TRUC_SCORE_MULTIPLIER
    score += truc_delta
    if truc_delta > 0:
        reasons.append(f"Trực {day_info['truc_name']} — ngày tốt (+{truc_delta})")
    elif truc_delta < 0:
        reasons.append(f"Trực {day_info['truc_name']} — ngày xấu ({truc_delta})")

    # 1b. Trực intent preference/forbid (from intent-rules.json)
    truc_idx = day_info.get("truc_idx")
    preferred_truc = intent_rule.get("preferred_truc", [])
    forbidden_truc = intent_rule.get("forbidden_truc", [])
    if truc_idx is not None:
        if truc_idx in preferred_truc:
            score += BONUS["truc_preferred"]
            reasons.append(
                f"Trực {day_info['truc_name']} — hợp với {_intent_label(intent)} "
                f"(+{BONUS['truc_preferred']})"
            )
        elif truc_idx in forbidden_truc:
            score += PENALTY["truc_forbidden"]
            penalty_sao.append(f"Trực {day_info['truc_name']}")
            reasons.append(
                f"Trực {day_info['truc_name']} — KỴ {_intent_label(intent)} "
                f"({PENALTY['truc_forbidden']})"
            )

    # 2. Universal cát tinh
    if day_info.get("has_thien_duc"):
        score += BONUS["thien_duc"]
        bonus_sao.append("Thiên Đức")
        reasons.append(f"Ngày có Thiên Đức (+{BONUS['thien_duc']})")

    if day_info.get("has_thien_duc_hop"):
        score += BONUS["thien_duc_hop"]
        bonus_sao.append("Thiên Đức Hợp")
        reasons.append(f"Ngày có Thiên Đức Hợp (+{BONUS['thien_duc_hop']})")

    # SPECIAL RULE 1: Nguyệt Đức ngoại lệ KIEN_TUNG
    if day_info.get("has_nguyet_duc"):
        if _nguyet_duc_bonus_applies(intent):
            score += BONUS["nguyet_duc"]
            bonus_sao.append("Nguyệt Đức")
            reasons.append(f"Ngày có Nguyệt Đức (+{BONUS['nguyet_duc']})")
        else:
            reasons.append(
                f"Nguyệt Đức — không tính điểm cho {_intent_label(intent)} (theo Ngọc Hạp Thông Thư)"
            )

    if day_info.get("has_nguyet_duc_hop"):
        if _nguyet_duc_bonus_applies(intent):
            score += BONUS["nguyet_duc_hop"]
            bonus_sao.append("Nguyệt Đức Hợp")
            reasons.append(f"Ngày có Nguyệt Đức Hợp (+{BONUS['nguyet_duc_hop']})")

    # 3. Element matching: Dụng Thần (advanced) or Dương Thần (simplified)
    day_hanh = day_info.get("day_nap_am_hanh")

    if user_chart.get("dung_than"):
        # ── Tứ Trụ mode: Dụng Thần / Hỷ Thần / Kỵ Thần v2 ──
        dm_name = user_chart.get("nhat_chu", {}).get("can_name", "")

        if day_hanh == user_chart["dung_than"]:
            score += BONUS["dung_than_match"]
            bonus_sao.append("Dụng Thần")
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Dụng Thần của "
                f"Nhật Chủ {dm_name} (+{BONUS['dung_than_match']})"
            )
        elif day_hanh == user_chart.get("hi_than"):
            score += BONUS["hi_than_match"]
            bonus_sao.append("Hỷ Thần")
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Hỷ Thần của "
                f"Nhật Chủ {dm_name} (+{BONUS['hi_than_match']})"
            )
        elif day_hanh == user_chart.get("ky_than_v2"):
            score += PENALTY["ky_than_v2_match"]
            penalty_sao.append("Kỵ Thần")
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Kỵ Thần của "
                f"Nhật Chủ {dm_name} ({PENALTY['ky_than_v2_match']})"
            )
        elif day_hanh == user_chart.get("cuu_than"):
            score += PENALTY["cuu_than_match"]
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Cừu Thần của "
                f"Nhật Chủ {dm_name} ({PENALTY['cuu_than_match']})"
            )
    else:
        # ── Simplified mode: Dương Thần (year Nạp Âm) ──
        if day_hanh == user_chart.get("duong_than"):
            score += BONUS["duong_than_match"]
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Dương Thần "
                f"của mệnh {user_chart['menh_name']} (+{BONUS['duong_than_match']})"
            )

    # 4. Layer 2 severity penalty
    if filter_result.get("severity") == 2:
        score += PENALTY["layer2_severity2"]
        for r in filter_result.get("reasons", []):
            reasons.append(f"{r} ({PENALTY['layer2_severity2']})")

    # 5. SPECIAL RULE 2: Thiên Xá nghịch lý
    thien_xa_detector = SAO_DETECTORS.get("thienXa")
    if thien_xa_detector and thien_xa_detector(day_info, user_chart):
        if intent in THIEN_XA_BONUS_INTENTS:
            score += BONUS["thien_xa_bonus"]
            bonus_sao.append("Thiên Xá")
            reasons.append(
                f"Ngày có Thiên Xá — cát tinh cho {_intent_label(intent)} (+{BONUS['thien_xa_bonus']})"
            )
        elif intent in THIEN_XA_PENALTY_INTENTS:
            score += PENALTY["thien_xa_penalty"]
            penalty_sao.append("Thiên Xá")
            reasons.append(
                f"Ngày có Thiên Xá — KỴ {_intent_label(intent)} "
                f"theo Ngọc Hạp Thông Thư ({PENALTY['thien_xa_penalty']})"
            )

    # 6. Intent-specific bonus_sao
    skip_keys = {"thienXa", "nguyetDuc", "nguyetDucHop", "thienDuc", "thienDucHop"}
    for sao_key in intent_rule.get("bonus_sao", []):
        if sao_key in skip_keys:
            continue
        detector = SAO_DETECTORS.get(sao_key)
        if detector and detector(day_info, user_chart):
            score += BONUS["intent_bonus"]
            bonus_sao.append(_sao_label(sao_key))
            reasons.append(
                f"Cát tinh {_sao_label(sao_key)} — tốt cho {_intent_label(intent)} (+{BONUS['intent_bonus']})"
            )

    # 7. Intent-specific forbidden_sao
    for sao_key in intent_rule.get("forbidden_sao", []):
        if sao_key == "thienXa":
            continue
        detector = SAO_DETECTORS.get(sao_key)
        if detector and detector(day_info, user_chart):
            score += PENALTY["intent_penalty"]
            penalty_sao.append(_sao_label(sao_key))
            reasons.append(
                f"Hung tinh {_sao_label(sao_key)} — kỵ {_intent_label(intent)} ({PENALTY['intent_penalty']})"
            )

    # 8. Thập Thần intent alignment (Tứ Trụ mode only)
    if user_chart.get("nhat_chu"):
        from engine.thap_than import get_day_god_for_intent
        dm_can = user_chart["nhat_chu"]["can_idx"]
        day_god = get_day_god_for_intent(day_info["day_can_idx"], dm_can, intent)
        if day_god:
            score += BONUS["thap_than_intent"]
            reasons.append(
                f"Ngày {day_god['name']} — hợp với {_intent_label(intent)} "
                f"(+{BONUS['thap_than_intent']})"
            )

    # 9. Đại Vận element alignment (Tứ Trụ + gender mode only)
    current_dv = user_chart.get("current_dai_van")
    if current_dv and user_chart.get("dung_than"):
        dv_hanh = current_dv.get("can_hanh")
        dung_than = user_chart["dung_than"]
        hi_than = user_chart.get("hi_than")

        if dv_hanh == dung_than or dv_hanh == hi_than:
            score += BONUS["dai_van_favorable"]
            reasons.append(
                f"Đại Vận {current_dv['display']} ({dv_hanh}) hỗ trợ Dụng Thần "
                f"(+{BONUS['dai_van_favorable']})"
            )
        elif dv_hanh == user_chart.get("ky_than_v2"):
            score += PENALTY["dai_van_unfavorable"]
            reasons.append(
                f"Đại Vận {current_dv['display']} ({dv_hanh}) là Kỵ Thần "
                f"({PENALTY['dai_van_unfavorable']})"
            )

    # 10. Grade
    if score >= GRADE_THRESHOLDS["A"]:
        grade = "A"
    elif score >= GRADE_THRESHOLDS["B"]:
        grade = "B"
    elif score >= GRADE_THRESHOLDS["C"]:
        grade = "C"
    else:
        grade = "D"

    return {
        "score": score,
        "grade": grade,
        "bonus_sao": bonus_sao,
        "penalty_sao": penalty_sao,
        "reasons_vi": reasons,
    }
