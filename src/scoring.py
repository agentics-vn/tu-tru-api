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
    check_cat_khanh,
    check_cuu_khong,
    check_cuu_tho_quy,
    check_dai_hao,
    check_dia_pha,
    check_dia_tac,
    check_dia_tai,
    check_dich_ma,
    check_giai_than,
    check_ha_khoi_cau_giao,
    check_hoa_tai,
    check_hoang_sa,
    check_ich_hau,
    check_kinh_tam,
    check_loc_kho,
    check_loi_cong,
    check_luc_bat_thanh,
    check_luc_hop,
    check_mau_thuong,
    check_minh_tinh,
    check_ngu_quy,
    check_nguyet_an,
    check_nguyet_hoa,
    check_nguyet_hoa_doc_hoa,
    check_nguyet_kien_chuyen_sat,
    check_nguyet_khong,
    check_nguyet_sat,
    check_nguyet_tai,
    check_nguyet_yem_dai_hoa,
    check_nhan_cach,
    check_phi_ma_sat,
    check_pho_ho,
    check_phuc_hau,
    check_phuc_sinh,
    check_quy_coc,
    check_sat_chu,
    check_sinh_khi,
    check_tam_hop,
    check_than_cach,
    check_thanh_tam,
    check_thien_an,
    check_thien_cuong,
    check_thien_dia_chuyen_sat,
    check_thien_hy,
    check_thien_ma,
    check_thien_nguc_thien_hoa,
    check_thien_phu,
    check_thien_phuc,
    check_thien_quan,
    check_thien_tac,
    check_thien_tai,
    check_thien_thanh,
    check_thien_xa,
    check_tho_cam,
    check_tho_on,
    check_tho_phu,
    check_tho_tu,
    check_thien_quy,
    check_tieu_hao,
    check_trung_tang,
    check_tuc_the,
    check_vang_vong,
    check_yeu_yen,
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

def _lm(d: dict) -> int:
    return d.get("lunar_month", 0)


def _dci(d: dict) -> int:
    return d.get("day_chi_idx", -1)


def _dcani(d: dict) -> int:
    return d.get("day_can_idx", -1)


def _yci(u: dict | None) -> int:
    return (u or {}).get("year_chi_idx", -1)


SAO_DETECTORS: dict[str, callable] = {
    # ── Pre-computed in day_info ──────────────────────────────────────────
    "thienDuc": lambda d, u=None: d.get("has_thien_duc", False),
    "thienDucHop": lambda d, u=None: d.get("has_thien_duc_hop", False),
    "nguyetDuc": lambda d, u=None: d.get("has_nguyet_duc", False),
    "nguyetDucHop": lambda d, u=None: d.get("has_nguyet_duc_hop", False),
    "duongThanMatch": lambda d, u: d.get("day_nap_am_hanh") == (u or {}).get("duong_than"),
    "tamNuong": lambda d, u=None: d.get("is_tam_nuong", False),
    "nguyetKy": lambda d, u=None: d.get("is_nguyet_ky", False),
    "duongCongKy": lambda d, u=None: d.get("is_duong_cong_ky", False),
    "thienXa": lambda d, u=None: d.get("has_thien_xa", False),

    # ── Implemented on-the-fly from day_info fields ───────────────────────
    "thoTu": lambda d, u=None: check_tho_tu(_lm(d), _dci(d)),
    "giaiThan": lambda d, u=None: check_giai_than(_lm(d), _dci(d)),
    "thienAn": lambda d, u=None: check_thien_an(_dcani(d), _dci(d)),
    "thienPhuc": lambda d, u=None: check_thien_phuc(_lm(d), _dci(d)),
    "dichMa": lambda d, u=None: check_dich_ma(_dci(d), _yci(u)),
    "nguyetSat": lambda d, u=None: check_nguyet_sat(_lm(d), _dci(d)),
    "thienCuong": lambda d, u=None: check_thien_cuong(_lm(d), _dci(d)),
    "daiHao": lambda d, u=None: check_dai_hao(_lm(d), _dci(d)),
    "satChu": lambda d, u=None: check_sat_chu(_lm(d), _dci(d)),
    "thienTac": lambda d, u=None: check_thien_tac(_lm(d), _dci(d)),
    "thienNgucThienHoa": lambda d, u=None: check_thien_nguc_thien_hoa(_lm(d), _dci(d)),
    # New — implemented in sao_ngay.py
    "sinhKhi": lambda d, u=None: check_sinh_khi(_lm(d), _dci(d)),
    "thienHy": lambda d, u=None: check_thien_hy(_lm(d), _dci(d)),
    "tieuHao": lambda d, u=None: check_tieu_hao(_lm(d), _dci(d)),
    "vatVong": lambda d, u=None: check_vang_vong(_lm(d), _dci(d)),
    "cuuKhong": lambda d, u=None: check_cuu_khong(_lm(d), _dci(d)),
    "lucBatThanh": lambda d, u=None: check_luc_bat_thanh(_lm(d), _dci(d)),
    "diaTac": lambda d, u=None: check_dia_tac(_lm(d), _dci(d)),
    "nguyetHoa": lambda d, u=None: check_nguyet_hoa(_lm(d), _dci(d)),
    "thoOn": lambda d, u=None: check_tho_on(_lm(d), _dci(d)),
    "thoPhU": lambda d, u=None: check_tho_phu(_lm(d), _dci(d)),
    "lucHop": lambda d, u=None: check_luc_hop(_dci(d), _yci(u)),
    "tamHop": lambda d, u=None: check_tam_hop(_dci(d), _yci(u)),

    # ── Batch 2: Implemented with traditional almanac formulas ────────────
    # Cát tinh
    "thienPhu": lambda d, u=None: check_thien_phu(_lm(d), _dci(d)),
    "thienTai": lambda d, u=None: check_thien_tai(_lm(d), _dci(d)),
    "diaTai": lambda d, u=None: check_dia_tai(_lm(d), _dci(d)),
    "nguyetTai": lambda d, u=None: check_nguyet_tai(_lm(d), _dci(d)),
    "locKho": lambda d, u=None: check_loc_kho(_lm(d), _dci(d)),
    "thienQuy": lambda d, u=None: check_thien_quy(_lm(d), _dcani(d)),
    "catKhanh": lambda d, u=None: check_cat_khanh(_lm(d), _dci(d)),
    "ichHau": lambda d, u=None: check_ich_hau(_lm(d), _dci(d)),
    "tucThe": lambda d, u=None: check_tuc_the(_lm(d), _dci(d)),
    "yeuYen": lambda d, u=None: check_yeu_yen(_lm(d), _dci(d)),
    "phoHo": lambda d, u=None: check_pho_ho(_lm(d), _dci(d)),
    "thienMa": lambda d, u=None: check_thien_ma(_lm(d), _dci(d)),
    "mauThuong": lambda d, u=None: check_mau_thuong(_dcani(d)),
    "phucHau": lambda d, u=None: check_phuc_hau(_lm(d), _dci(d)),
    "thanhTam": lambda d, u=None: check_thanh_tam(_lm(d), _dci(d)),
    "thienQuan": lambda d, u=None: check_thien_quan(_lm(d), _dci(d)),
    "minhTinh": lambda d, u=None: check_minh_tinh(_lm(d), _dci(d)),
    "kinhTam": lambda d, u=None: check_kinh_tam(_lm(d), _dci(d)),
    "phucSinh": lambda d, u=None: check_phuc_sinh(_lm(d), _dci(d)),
    "nguyetAn": lambda d, u=None: check_nguyet_an(_lm(d), _dcani(d)),
    "thienThanh": lambda d, u=None: check_thien_thanh(_lm(d), _dci(d)),
    "nguyetKhong": lambda d, u=None: check_nguyet_khong(_lm(d), _dcani(d)),
    # Hung tinh
    "nhanCach": lambda d, u=None: check_nhan_cach(_lm(d), _dci(d)),
    "phiMaSat": lambda d, u=None: check_phi_ma_sat(_lm(d), _dci(d)),
    "nguyetYemDaiHoa": lambda d, u=None: check_nguyet_yem_dai_hoa(_lm(d), _dci(d)),
    "thoCam": lambda d, u=None: check_tho_cam(_lm(d), _dci(d)),
    "cuuThoQuy": lambda d, u=None: check_cuu_tho_quy(_lm(d), _dcani(d), _dci(d)),
    "thienDiaChuyenSat": lambda d, u=None: check_thien_dia_chuyen_sat(_lm(d), _dci(d)),
    "nguyetKienChuyenSat": lambda d, u=None: check_nguyet_kien_chuyen_sat(_lm(d), _dci(d)),
    "haKhoiCauGiao": lambda d, u=None: check_ha_khoi_cau_giao(_lm(d), _dci(d)),
    "hoaTai": lambda d, u=None: check_hoa_tai(_lm(d), _dci(d)),
    "trungTang": lambda d, u=None: check_trung_tang(_lm(d), _dcani(d)),
    "quyCoc": lambda d, u=None: check_quy_coc(_lm(d), _dci(d)),
    "thanCach": lambda d, u=None: check_than_cach(_lm(d), _dci(d)),
    "hoangSa": lambda d, u=None: check_hoang_sa(_lm(d), _dci(d)),
    "nguNguyQuiet": lambda d, u=None: check_ngu_quy(_lm(d), _dci(d)),
    "nguyetHoaDockHoa": lambda d, u=None: check_nguyet_hoa_doc_hoa(_lm(d), _dci(d)),
    "loiCong": lambda d, u=None: check_loi_cong(_lm(d), _dci(d)),
    "diaPha": lambda d, u=None: check_dia_pha(_lm(d), _dci(d))
}

# ─────────────────────────────────────────────────────────────────────────────
# SAO LABELS
# ─────────────────────────────────────────────────────────────────────────────

SAO_LABELS: dict[str, str] = {
    # Cát tinh
    "thienDuc": "Thiên Đức", "thienDucHop": "Thiên Đức Hợp",
    "nguyetDuc": "Nguyệt Đức", "nguyetDucHop": "Nguyệt Đức Hợp",
    "thienXa": "Thiên Xá", "sinhKhi": "Sinh Khí",
    "thienHy": "Thiên Hỷ", "thienPhu": "Thiên Phú",
    "thienTai": "Thiên Tài", "diaTai": "Địa Tài",
    "nguyetTai": "Nguyệt Tài", "locKho": "Lộc Khố",
    "thienMa": "Thiên Mã", "dichMa": "Dịch Mã",
    "phoHo": "Phổ Hộ", "ichHau": "Ích Hậu",
    "catKhanh": "Cát Khánh", "thienPhuc": "Thiên Phúc",
    "thienQuy": "Thiên Quý", "giaiThan": "Giải Thần",
    "tucThe": "Tục Thế", "yeuYen": "Yếu Yên",
    "thienAn": "Thiên Ân", "lucHop": "Lục Hợp",
    "tamHop": "Tam Hợp", "mauThuong": "Mậu Thương",
    "phucHau": "Phúc Hậu", "thanhTam": "Thánh Tâm",
    "thienQuan": "Thiên Quan", "minhTinh": "Minh Tinh",
    "kinhTam": "Kính Tâm", "phucSinh": "Phúc Sinh",
    "nguyetAn": "Nguyệt Ân", "thienThanh": "Thiên Thanh",
    "nguyetKhong": "Nguyệt Không",
    # Hung tinh
    "tamNuong": "Tam Nương", "nguyetKy": "Nguyệt Kỵ",
    "duongCongKy": "Dương Công Kỵ",
    "thienTac": "Thiên Tặc", "diaTac": "Địa Tặc",
    "thienCuong": "Thiên Cương", "daiHao": "Đại Hao",
    "tieuHao": "Tiểu Hao", "nguyetSat": "Nguyệt Sát",
    "nguyetHoa": "Nguyệt Hỏa", "vatVong": "Vãng Vong",
    "cuuKhong": "Cửu Không", "lucBatThanh": "Lục Bất Thành",
    "nhanCach": "Nhân Cách", "phiMaSat": "Phi Ma Sát",
    "thoTu": "Thọ Tử", "satChu": "Sát Chủ",
    "thienNgucThienHoa": "Thiên Ngục/Thiên Hỏa",
    "thoOn": "Thổ Ôn", "thoPhU": "Thổ Phủ",
    "thoCam": "Thổ Cấm", "cuuThoQuy": "Cửu Thổ Quỷ",
    "nguyetYemDaiHoa": "Nguyệt Yếm Đại Họa",
    "thienDiaChuyenSat": "Thiên Địa Chuyển Sát",
    "nguyetKienChuyenSat": "Nguyệt Kiến Chuyển Sát",
    "haKhoiCauGiao": "Hà Khôi Câu Giảo",
    "hoaTai": "Hỏa Tai", "trungTang": "Trùng Tang",
    "quyCoc": "Quỷ Cốc", "thanCach": "Thần Cách",
    "hoangSa": "Hoàng Sa", "nguNguyQuiet": "Ngũ Quỷ",
    "nguyetHoaDockHoa": "Nguyệt Hỏa Độc Hỏa",
    "loiCong": "Lôi Công", "diaPha": "Địa Phá",
}

from filter import INTENT_LABELS  # single source of truth


def _intent_label(intent: str) -> str:
    return INTENT_LABELS.get(intent, intent)


def _sao_label(key: str) -> str:
    return SAO_LABELS.get(key, key)


def _nguyet_duc_bonus_applies(intent: str) -> bool:
    """SPECIAL RULE 1: Nguyệt Đức excluded from KIEN_TUNG."""
    return intent != "KIEN_TUNG"


# ─────────────────────────────────────────────────────────────────────────────
# PLAIN-LANGUAGE EXPLANATIONS (for non-expert users)
# ─────────────────────────────────────────────────────────────────────────────

SAO_PLAIN: dict[str, str] = {
    # Cát tinh
    "thienDuc": "được quý nhân phù trợ, mọi việc thuận lợi",
    "thienDucHop": "có quý nhân hỗ trợ",
    "nguyetDuc": "được phúc lành che chở, gặp dữ hóa lành",
    "nguyetDucHop": "có phúc đức hỗ trợ",
    "thienXa": "ngày được ân xá, giải trừ tai ương",
    "thienAn": "ngày được trời ban ân huệ, thuận lợi",
    "thienPhuc": "ngày có phúc lành từ trời",
    "giaiThan": "có thần giải trừ bệnh tật, tốt cho chữa bệnh",
    "dichMa": "thuận lợi cho di chuyển, thay đổi",
    "sinhKhi": "ngày có sinh khí vượng, tốt cho khởi đầu",
    "thienHy": "ngày có hỷ khí, tốt cho hôn nhân và việc vui",
    "lucHop": "ngày hợp tuổi, thuận lợi cho mọi việc",
    "tamHop": "ngày tam hợp tuổi, rất thuận lợi",
    # Hung tinh
    "thoTu": "ngày rất xấu cho phẫu thuật theo quan niệm truyền thống",
    "thienCuong": "ngày có sao dữ, bách sự không nên",
    "daiHao": "ngày dễ hao tốn, tổn thất",
    "tieuHao": "ngày dễ hao tốn nhỏ",
    "nguyetSat": "ngày xung khắc với tháng, không thuận lợi",
    "satChu": "ngày có sao sát, kiêng phẫu thuật",
    "thienTac": "ngày có sao trộm cắp, kiêng xây dựng",
    "diaTac": "ngày có sao trộm cắp (đất), kiêng xây dựng",
    "thienNgucThienHoa": "ngày có sao ngục tù và hỏa hoạn, cần cẩn thận",
    "tamNuong": "ngày Tam Nương, bách sự kiêng kỵ",
    "nguyetKy": "ngày kiêng kỵ trong tháng",
    "duongCongKy": "ngày Dương Công kỵ, không nên làm việc lớn",
    "vatVong": "ngày Vãng Vong, kiêng xuất hành",
    "cuuKhong": "ngày Cửu Không, sự việc khó thành",
    "lucBatThanh": "ngày Lục Bất Thành, sự việc không thành",
    "nguyetHoa": "ngày có sao Nguyệt Hỏa, kiêng lửa/bếp",
    "thoOn": "ngày có sao đất xấu, kiêng xây dựng/đào đất",
    "thoPhU": "ngày có sao đất xấu, kiêng xây dựng",
    # Batch 2 — cát tinh
    "nguyetAn": "ngày được tháng ban ân huệ, thuận lợi mọi việc",
    "thienThanh": "ngày thiên thành, thuận lợi cho khởi sự",
    "thienPhu": "ngày có phú quý từ trời, tốt cho kinh doanh",
    "thienTai": "ngày có tài lộc từ trời, tốt cho cầu tài",
    "diaTai": "ngày có tài lộc từ đất, tốt cho buôn bán",
    "nguyetTai": "ngày có tài lộc trong tháng",
    "locKho": "ngày mở kho lộc, tốt cho tài chính",
    "thienQuy": "ngày có quý nhân phù trợ",
    "catKhanh": "ngày cát khánh, tốt cho việc vui mừng",
    "ichHau": "ngày ích hậu, mang lại lợi ích lâu dài",
    "tucThe": "ngày tục thế, tốt cho con cháu",
    "yeuYen": "ngày yên ổn, thuận lợi",
    "phoHo": "ngày được bảo hộ rộng rãi",
    "thienMa": "ngày thiên mã, tốt cho di chuyển",
    "mauThuong": "ngày mậu thương, tốt cho kinh doanh",
    "phucHau": "ngày phúc hậu, tích phúc đức",
    "thanhTam": "ngày thánh tâm, thuận lợi cho tế tự",
    "thienQuan": "ngày thiên quan, tốt cho công danh",
    "minhTinh": "ngày minh tinh, sáng suốt thuận lợi",
    "kinhTam": "ngày kính tâm, tốt cho lễ bái",
    "phucSinh": "ngày phúc sinh, tốt cho khởi đầu mới",
    "nguyetKhong": "ngày nguyệt không, tốt cho tu hành/thanh tịnh",
    # Batch 2 — hung tinh
    "nhanCach": "ngày nhân cách, kiêng gặp gỡ/hôn nhân",
    "phiMaSat": "ngày phi ma sát, kiêng di chuyển",
    "nguyetYemDaiHoa": "ngày nguyệt yếm đại họa, kiêng việc lớn",
    "thoCam": "ngày thổ cấm, kiêng đào đất/xây dựng",
    "cuuThoQuy": "ngày cửu thổ quỷ, kiêng xây dựng/đào đất",
    "thienDiaChuyenSat": "ngày thiên địa chuyển sát, kiêng khởi công",
    "nguyetKienChuyenSat": "ngày phá, không thuận lợi cho khởi sự",
    "haKhoiCauGiao": "ngày hà khôi, kiêng kiện tụng",
    "hoaTai": "ngày hỏa tai, kiêng lửa/bếp",
    "trungTang": "ngày trùng tang, kiêng an táng",
    "quyCoc": "ngày quỷ cốc, kiêng tang lễ",
    "thanCach": "ngày thần cách, kiêng tế tự",
    "hoangSa": "ngày hoàng sa, kiêng xuất hành",
    "nguNguyQuiet": "ngày ngũ quỷ, kiêng mọi việc lớn",
    "nguyetHoaDockHoa": "ngày nguyệt hỏa độc hỏa, kiêng lửa",
    "loiCong": "ngày lôi công, kiêng xây dựng/sửa chữa",
    "diaPha": "ngày địa phá, kiêng xây dựng/khởi công",
}

ELEMENT_PLAIN: dict[str, str] = {
    "Kim": "Kim (kim loại)",
    "Mộc": "Mộc (cây cỏ)",
    "Thủy": "Thủy (nước)",
    "Hỏa": "Hỏa (lửa)",
    "Thổ": "Thổ (đất)",
}

GRADE_PLAIN: dict[str, str] = {
    "A": "Rất tốt — nên chọn ngày này",
    "B": "Tốt — có thể chọn",
    "C": "Bình thường — chấp nhận được nếu không có lựa chọn khác",
    "D": "Không tốt — nên tránh",
}


def _build_summary_vi(
    day_info: dict,
    user_chart: dict,
    intent: str,
    grade: str,
    bonus_sao: list[str],
    penalty_sao: list[str],
    plain_pros: list[str],
    plain_cons: list[str],
) -> str:
    """Build a plain-language summary that non-experts can understand."""
    intent_name = _intent_label(intent)
    parts: list[str] = []

    # Opening — grade
    parts.append(GRADE_PLAIN.get(grade, "") + ".")

    # Pros
    if plain_pros:
        parts.append("Điểm tốt: " + "; ".join(plain_pros) + ".")

    # Cons
    if plain_cons:
        parts.append("Lưu ý: " + "; ".join(plain_cons) + ".")

    return " ".join(parts)


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
    plain_pros: list[str] = []
    plain_cons: list[str] = []

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
            plain_pros.append(f"ngày thuộc loại hợp với việc {_intent_label(intent).lower()}")
        elif truc_idx in forbidden_truc:
            score += PENALTY["truc_forbidden"]
            penalty_sao.append(f"Trực {day_info['truc_name']}")
            reasons.append(
                f"Trực {day_info['truc_name']} — KỴ {_intent_label(intent)} "
                f"({PENALTY['truc_forbidden']})"
            )
            plain_cons.append(f"ngày thuộc loại kiêng kỵ cho việc {_intent_label(intent).lower()}")

    # 2. Universal cát tinh
    if day_info.get("has_thien_duc"):
        score += BONUS["thien_duc"]
        bonus_sao.append("Thiên Đức")
        reasons.append(f"Ngày có Thiên Đức (+{BONUS['thien_duc']})")
        plain_pros.append(SAO_PLAIN["thienDuc"])

    if day_info.get("has_thien_duc_hop"):
        score += BONUS["thien_duc_hop"]
        bonus_sao.append("Thiên Đức Hợp")
        reasons.append(f"Ngày có Thiên Đức Hợp (+{BONUS['thien_duc_hop']})")
        plain_pros.append(SAO_PLAIN["thienDucHop"])

    # SPECIAL RULE 1: Nguyệt Đức ngoại lệ KIEN_TUNG
    if day_info.get("has_nguyet_duc"):
        if _nguyet_duc_bonus_applies(intent):
            score += BONUS["nguyet_duc"]
            bonus_sao.append("Nguyệt Đức")
            reasons.append(f"Ngày có Nguyệt Đức (+{BONUS['nguyet_duc']})")
            plain_pros.append(SAO_PLAIN["nguyetDuc"])
        else:
            reasons.append(
                f"Nguyệt Đức — không tính điểm cho {_intent_label(intent)} (theo Ngọc Hạp Thông Thư)"
            )

    if day_info.get("has_nguyet_duc_hop"):
        if _nguyet_duc_bonus_applies(intent):
            score += BONUS["nguyet_duc_hop"]
            bonus_sao.append("Nguyệt Đức Hợp")
            reasons.append(f"Ngày có Nguyệt Đức Hợp (+{BONUS['nguyet_duc_hop']})")
            plain_pros.append(SAO_PLAIN["nguyetDucHop"])
        else:
            reasons.append(
                f"Nguyệt Đức Hợp — không tính điểm cho {_intent_label(intent)} (theo Ngọc Hạp Thông Thư)"
            )

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
            plain_pros.append(
                f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) "
                f"rất hợp với mệnh bạn, bổ trợ sức khỏe"
            )
        elif day_hanh == user_chart.get("hi_than"):
            score += BONUS["hi_than_match"]
            bonus_sao.append("Hỷ Thần")
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Hỷ Thần của "
                f"Nhật Chủ {dm_name} (+{BONUS['hi_than_match']})"
            )
            plain_pros.append(
                f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) "
                f"tương hợp với mệnh bạn"
            )
        elif day_hanh == user_chart.get("ky_than_v2"):
            score += PENALTY["ky_than_v2_match"]
            penalty_sao.append("Kỵ Thần")
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Kỵ Thần của "
                f"Nhật Chủ {dm_name} ({PENALTY['ky_than_v2_match']})"
            )
            plain_cons.append(
                f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) "
                f"xung khắc với mệnh bạn"
            )
        elif day_hanh == user_chart.get("cuu_than"):
            score += PENALTY["cuu_than_match"]
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Cừu Thần của "
                f"Nhật Chủ {dm_name} ({PENALTY['cuu_than_match']})"
            )
            plain_cons.append(
                f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) "
                f"không thuận lợi cho mệnh bạn"
            )
    else:
        # ── Simplified mode: Dương Thần (year Nạp Âm) ──
        if day_hanh == user_chart.get("duong_than"):
            score += BONUS["duong_than_match"]
            reasons.append(
                f"Nạp Âm ngày ({day_hanh}) là Dương Thần "
                f"của mệnh {user_chart['menh_name']} (+{BONUS['duong_than_match']})"
            )
            plain_pros.append(
                f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) "
                f"hợp với mệnh bạn"
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
            plain_pros.append(SAO_PLAIN["thienXa"])
        elif intent in THIEN_XA_PENALTY_INTENTS:
            score += PENALTY["thien_xa_penalty"]
            penalty_sao.append("Thiên Xá")
            reasons.append(
                f"Ngày có Thiên Xá — KỴ {_intent_label(intent)} "
                f"theo Ngọc Hạp Thông Thư ({PENALTY['thien_xa_penalty']})"
            )
            plain_cons.append(f"ngày không phù hợp cho việc {_intent_label(intent).lower()}")

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
            plain = SAO_PLAIN.get(sao_key)
            if plain:
                plain_pros.append(plain)

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
            plain = SAO_PLAIN.get(sao_key)
            if plain:
                plain_cons.append(plain)

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
            plain_pros.append(f"mối quan hệ ngũ hành ngày hỗ trợ tốt cho việc {_intent_label(intent).lower()}")

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
            plain_pros.append("vận may giai đoạn hiện tại đang thuận lợi")
        elif dv_hanh == user_chart.get("ky_than_v2"):
            score += PENALTY["dai_van_unfavorable"]
            reasons.append(
                f"Đại Vận {current_dv['display']} ({dv_hanh}) là Kỵ Thần "
                f"({PENALTY['dai_van_unfavorable']})"
            )
            plain_cons.append("vận may giai đoạn hiện tại không thuận, nên cẩn thận hơn")
        elif dv_hanh == user_chart.get("cuu_than"):
            score += PENALTY["dai_van_unfavorable"]
            reasons.append(
                f"Đại Vận {current_dv['display']} ({dv_hanh}) là Cừu Thần "
                f"({PENALTY['dai_van_unfavorable']})"
            )
            plain_cons.append("vận may giai đoạn hiện tại không thuận, nên cẩn thận hơn")

    # 10. Clamp + Grade
    score = max(0, min(100, score))

    if score >= GRADE_THRESHOLDS["A"]:
        grade = "A"
    elif score >= GRADE_THRESHOLDS["B"]:
        grade = "B"
    elif score >= GRADE_THRESHOLDS["C"]:
        grade = "C"
    else:
        grade = "D"

    summary_vi = _build_summary_vi(
        day_info, user_chart, intent, grade,
        bonus_sao, penalty_sao, plain_pros, plain_cons,
    )

    return {
        "score": score,
        "grade": grade,
        "bonus_sao": bonus_sao,
        "penalty_sao": penalty_sao,
        "reasons_vi": reasons,
        "summary_vi": summary_vi,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DETAILED SCORE BREAKDOWN (for /v1/chon-ngay/detail)
# ─────────────────────────────────────────────────────────────────────────────

def compute_score_breakdown(
    day_info: dict,
    user_chart: dict,
    intent: str,
    intent_rule: dict,
    filter_result: dict,
) -> dict:
    """
    Compute score with a detailed breakdown of each scoring component.

    Returns the same result as compute_score(), plus a 'breakdown' list
    where each item has: source, points, reason_vi, type ('bonus'|'penalty'|'neutral').
    """
    score = BASE_SCORE
    bonus_sao: list[str] = []
    penalty_sao: list[str] = []
    reasons: list[str] = []
    plain_pros: list[str] = []
    plain_cons: list[str] = []
    breakdown: list[dict] = []

    breakdown.append({
        "source": "Điểm cơ bản",
        "points": BASE_SCORE,
        "reason_vi": "Mọi ngày bắt đầu từ 50 điểm",
        "type": "neutral",
    })

    # 1. Trực score
    truc_delta = day_info["truc_score"] * TRUC_SCORE_MULTIPLIER
    score += truc_delta
    if truc_delta != 0:
        btype = "bonus" if truc_delta > 0 else "penalty"
        reason = f"Trực {day_info['truc_name']} — {'ngày tốt' if truc_delta > 0 else 'ngày xấu'}"
        reasons.append(f"{reason} ({'+' if truc_delta > 0 else ''}{truc_delta})")
        breakdown.append({"source": f"Trực {day_info['truc_name']}", "points": truc_delta, "reason_vi": reason, "type": btype})

    # 1b. Trực intent preference/forbid
    truc_idx = day_info.get("truc_idx")
    preferred_truc = intent_rule.get("preferred_truc", [])
    forbidden_truc = intent_rule.get("forbidden_truc", [])
    if truc_idx is not None:
        if truc_idx in preferred_truc:
            pts = BONUS["truc_preferred"]
            score += pts
            reason = f"Trực {day_info['truc_name']} — hợp với {_intent_label(intent)}"
            reasons.append(f"{reason} (+{pts})")
            plain_pros.append(f"ngày thuộc loại hợp với việc {_intent_label(intent).lower()}")
            breakdown.append({"source": f"Trực {day_info['truc_name']} (intent)", "points": pts, "reason_vi": reason, "type": "bonus"})
        elif truc_idx in forbidden_truc:
            pts = PENALTY["truc_forbidden"]
            score += pts
            penalty_sao.append(f"Trực {day_info['truc_name']}")
            reason = f"Trực {day_info['truc_name']} — KỴ {_intent_label(intent)}"
            reasons.append(f"{reason} ({pts})")
            plain_cons.append(f"ngày thuộc loại kiêng kỵ cho việc {_intent_label(intent).lower()}")
            breakdown.append({"source": f"Trực {day_info['truc_name']} (intent)", "points": pts, "reason_vi": reason, "type": "penalty"})

    # 2. Universal cát tinh
    for field, key, sao_name, sao_key in [
        ("has_thien_duc", "thien_duc", "Thiên Đức", "thienDuc"),
        ("has_thien_duc_hop", "thien_duc_hop", "Thiên Đức Hợp", "thienDucHop"),
    ]:
        if day_info.get(field):
            pts = BONUS[key]
            score += pts
            bonus_sao.append(sao_name)
            reasons.append(f"Ngày có {sao_name} (+{pts})")
            plain_pros.append(SAO_PLAIN[sao_key])
            breakdown.append({"source": sao_name, "points": pts, "reason_vi": f"Ngày có {sao_name}", "type": "bonus"})

    # SPECIAL RULE 1: Nguyệt Đức
    if day_info.get("has_nguyet_duc"):
        if _nguyet_duc_bonus_applies(intent):
            pts = BONUS["nguyet_duc"]
            score += pts
            bonus_sao.append("Nguyệt Đức")
            reasons.append(f"Ngày có Nguyệt Đức (+{pts})")
            plain_pros.append(SAO_PLAIN["nguyetDuc"])
            breakdown.append({"source": "Nguyệt Đức", "points": pts, "reason_vi": "Ngày có Nguyệt Đức", "type": "bonus"})
        else:
            reason = f"Nguyệt Đức — không tính điểm cho {_intent_label(intent)} (theo Ngọc Hạp Thông Thư)"
            reasons.append(reason)
            breakdown.append({"source": "Nguyệt Đức", "points": 0, "reason_vi": reason, "type": "neutral"})

    if day_info.get("has_nguyet_duc_hop"):
        if _nguyet_duc_bonus_applies(intent):
            pts = BONUS["nguyet_duc_hop"]
            score += pts
            bonus_sao.append("Nguyệt Đức Hợp")
            reasons.append(f"Ngày có Nguyệt Đức Hợp (+{pts})")
            plain_pros.append(SAO_PLAIN["nguyetDucHop"])
            breakdown.append({"source": "Nguyệt Đức Hợp", "points": pts, "reason_vi": "Ngày có Nguyệt Đức Hợp", "type": "bonus"})
        else:
            reason = f"Nguyệt Đức Hợp — không tính điểm cho {_intent_label(intent)} (theo Ngọc Hạp Thông Thư)"
            reasons.append(reason)
            breakdown.append({"source": "Nguyệt Đức Hợp", "points": 0, "reason_vi": reason, "type": "neutral"})

    # 3. Element matching
    day_hanh = day_info.get("day_nap_am_hanh")

    if user_chart.get("dung_than"):
        dm_name = user_chart.get("nhat_chu", {}).get("can_name", "")
        if day_hanh == user_chart["dung_than"]:
            pts = BONUS["dung_than_match"]
            score += pts
            bonus_sao.append("Dụng Thần")
            reason = f"Nạp Âm ngày ({day_hanh}) là Dụng Thần của Nhật Chủ {dm_name}"
            reasons.append(f"{reason} (+{pts})")
            plain_pros.append(f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) rất hợp với mệnh bạn, bổ trợ sức khỏe")
            breakdown.append({"source": "Dụng Thần", "points": pts, "reason_vi": reason, "type": "bonus"})
        elif day_hanh == user_chart.get("hi_than"):
            pts = BONUS["hi_than_match"]
            score += pts
            bonus_sao.append("Hỷ Thần")
            reason = f"Nạp Âm ngày ({day_hanh}) là Hỷ Thần của Nhật Chủ {dm_name}"
            reasons.append(f"{reason} (+{pts})")
            plain_pros.append(f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) tương hợp với mệnh bạn")
            breakdown.append({"source": "Hỷ Thần", "points": pts, "reason_vi": reason, "type": "bonus"})
        elif day_hanh == user_chart.get("ky_than_v2"):
            pts = PENALTY["ky_than_v2_match"]
            score += pts
            penalty_sao.append("Kỵ Thần")
            reason = f"Nạp Âm ngày ({day_hanh}) là Kỵ Thần của Nhật Chủ {dm_name}"
            reasons.append(f"{reason} ({pts})")
            plain_cons.append(f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) xung khắc với mệnh bạn")
            breakdown.append({"source": "Kỵ Thần", "points": pts, "reason_vi": reason, "type": "penalty"})
        elif day_hanh == user_chart.get("cuu_than"):
            pts = PENALTY["cuu_than_match"]
            score += pts
            reason = f"Nạp Âm ngày ({day_hanh}) là Cừu Thần của Nhật Chủ {dm_name}"
            reasons.append(f"{reason} ({pts})")
            plain_cons.append(f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) không thuận lợi cho mệnh bạn")
            breakdown.append({"source": "Cừu Thần", "points": pts, "reason_vi": reason, "type": "penalty"})
    else:
        if day_hanh == user_chart.get("duong_than"):
            pts = BONUS["duong_than_match"]
            score += pts
            reason = f"Nạp Âm ngày ({day_hanh}) là Dương Thần của mệnh {user_chart['menh_name']}"
            reasons.append(f"{reason} (+{pts})")
            plain_pros.append(f"năng lượng ngày ({ELEMENT_PLAIN.get(day_hanh, day_hanh)}) hợp với mệnh bạn")
            breakdown.append({"source": "Dương Thần", "points": pts, "reason_vi": reason, "type": "bonus"})

    # 4. Layer 2 severity penalty
    if filter_result.get("severity") == 2:
        pts = PENALTY["layer2_severity2"]
        score += pts
        for r in filter_result.get("reasons", []):
            reasons.append(f"{r} ({pts})")
            breakdown.append({"source": "Cảnh báo Layer 2", "points": pts, "reason_vi": r, "type": "penalty"})

    # 5. SPECIAL RULE 2: Thiên Xá
    thien_xa_detector = SAO_DETECTORS.get("thienXa")
    if thien_xa_detector and thien_xa_detector(day_info, user_chart):
        if intent in THIEN_XA_BONUS_INTENTS:
            pts = BONUS["thien_xa_bonus"]
            score += pts
            bonus_sao.append("Thiên Xá")
            reason = f"Ngày có Thiên Xá — cát tinh cho {_intent_label(intent)}"
            reasons.append(f"{reason} (+{pts})")
            plain_pros.append(SAO_PLAIN["thienXa"])
            breakdown.append({"source": "Thiên Xá", "points": pts, "reason_vi": reason, "type": "bonus"})
        elif intent in THIEN_XA_PENALTY_INTENTS:
            pts = PENALTY["thien_xa_penalty"]
            score += pts
            penalty_sao.append("Thiên Xá")
            reason = f"Ngày có Thiên Xá — KỴ {_intent_label(intent)} theo Ngọc Hạp Thông Thư"
            reasons.append(f"{reason} ({pts})")
            plain_cons.append(f"ngày không phù hợp cho việc {_intent_label(intent).lower()}")
            breakdown.append({"source": "Thiên Xá", "points": pts, "reason_vi": reason, "type": "penalty"})

    # 6. Intent-specific bonus_sao
    skip_keys = {"thienXa", "nguyetDuc", "nguyetDucHop", "thienDuc", "thienDucHop"}
    for sao_key in intent_rule.get("bonus_sao", []):
        if sao_key in skip_keys:
            continue
        detector = SAO_DETECTORS.get(sao_key)
        if detector and detector(day_info, user_chart):
            pts = BONUS["intent_bonus"]
            score += pts
            label = _sao_label(sao_key)
            bonus_sao.append(label)
            reason = f"Cát tinh {label} — tốt cho {_intent_label(intent)}"
            reasons.append(f"{reason} (+{pts})")
            plain = SAO_PLAIN.get(sao_key)
            if plain:
                plain_pros.append(plain)
            breakdown.append({"source": label, "points": pts, "reason_vi": reason, "type": "bonus"})

    # 7. Intent-specific forbidden_sao
    for sao_key in intent_rule.get("forbidden_sao", []):
        if sao_key == "thienXa":
            continue
        detector = SAO_DETECTORS.get(sao_key)
        if detector and detector(day_info, user_chart):
            pts = PENALTY["intent_penalty"]
            score += pts
            label = _sao_label(sao_key)
            penalty_sao.append(label)
            reason = f"Hung tinh {label} — kỵ {_intent_label(intent)}"
            reasons.append(f"{reason} ({pts})")
            plain = SAO_PLAIN.get(sao_key)
            if plain:
                plain_cons.append(plain)
            breakdown.append({"source": label, "points": pts, "reason_vi": reason, "type": "penalty"})

    # 8. Thập Thần intent alignment
    if user_chart.get("nhat_chu"):
        from engine.thap_than import get_day_god_for_intent
        dm_can = user_chart["nhat_chu"]["can_idx"]
        day_god = get_day_god_for_intent(day_info["day_can_idx"], dm_can, intent)
        if day_god:
            pts = BONUS["thap_than_intent"]
            score += pts
            reason = f"Ngày {day_god['name']} — hợp với {_intent_label(intent)}"
            reasons.append(f"{reason} (+{pts})")
            plain_pros.append(f"mối quan hệ ngũ hành ngày hỗ trợ tốt cho việc {_intent_label(intent).lower()}")
            breakdown.append({"source": f"Thập Thần ({day_god['name']})", "points": pts, "reason_vi": reason, "type": "bonus"})

    # 9. Đại Vận
    current_dv = user_chart.get("current_dai_van")
    if current_dv and user_chart.get("dung_than"):
        dv_hanh = current_dv.get("can_hanh")
        dung_than = user_chart["dung_than"]
        hi_than = user_chart.get("hi_than")

        if dv_hanh == dung_than or dv_hanh == hi_than:
            pts = BONUS["dai_van_favorable"]
            score += pts
            reason = f"Đại Vận {current_dv['display']} ({dv_hanh}) hỗ trợ Dụng Thần"
            reasons.append(f"{reason} (+{pts})")
            plain_pros.append("vận may giai đoạn hiện tại đang thuận lợi")
            breakdown.append({"source": "Đại Vận", "points": pts, "reason_vi": reason, "type": "bonus"})
        elif dv_hanh == user_chart.get("ky_than_v2"):
            pts = PENALTY["dai_van_unfavorable"]
            score += pts
            reason = f"Đại Vận {current_dv['display']} ({dv_hanh}) là Kỵ Thần"
            reasons.append(f"{reason} ({pts})")
            plain_cons.append("vận may giai đoạn hiện tại không thuận, nên cẩn thận hơn")
            breakdown.append({"source": "Đại Vận", "points": pts, "reason_vi": reason, "type": "penalty"})
        elif dv_hanh == user_chart.get("cuu_than"):
            pts = PENALTY["dai_van_unfavorable"]
            score += pts
            reason = f"Đại Vận {current_dv['display']} ({dv_hanh}) là Cừu Thần"
            reasons.append(f"{reason} ({pts})")
            plain_cons.append("vận may giai đoạn hiện tại không thuận, nên cẩn thận hơn")
            breakdown.append({"source": "Đại Vận", "points": pts, "reason_vi": reason, "type": "penalty"})

    # 10. Clamp + Grade
    score = max(0, min(100, score))

    if score >= GRADE_THRESHOLDS["A"]:
        grade = "A"
    elif score >= GRADE_THRESHOLDS["B"]:
        grade = "B"
    elif score >= GRADE_THRESHOLDS["C"]:
        grade = "C"
    else:
        grade = "D"

    summary_vi = _build_summary_vi(
        day_info, user_chart, intent, grade,
        bonus_sao, penalty_sao, plain_pros, plain_cons,
    )

    return {
        "score": score,
        "grade": grade,
        "bonus_sao": bonus_sao,
        "penalty_sao": penalty_sao,
        "reasons_vi": reasons,
        "summary_vi": summary_vi,
        "breakdown": breakdown,
    }
