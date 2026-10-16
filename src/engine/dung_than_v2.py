"""
dung_than_v2.py — Dụng / Hỉ / Kỵ / Cừu / Nhàn theo luật ``2026-10.1``.

Chỉ chạy khi người gọi yêu cầu (``find_dung_than(..., rule="2026-10.1")``); mặc định engine
vẫn là v1 (``dung_than.py``), không đổi.

Nguồn sự thật: đặc tả ``2026-10-14-dung-ky-dac-ta-thuat-toan.md`` (repo nuoiconthuanmenh.vn,
``docs/superpowers/specs/``), mục 3–9; tóm tắt ở ``docs/algorithm.md`` §23. Bản cài thử kèm
đặc tả là đặc tả chạy được; module này viết lại cùng hằng, cùng thứ tự quyết định, và thêm
các trường hợp đồng 8.1 mà bản thử không trả (``rule_version``, ``cuong_nhuoc``,
``co.dung_vang``, ``ly_do``).

Nguyên tắc 1 của đặc tả: thuật toán chọn MỘT nhánh, nhánh tra MỘT dòng bảng, dòng bảng cho
cùng lúc mọi vai. Không vai nào tính bằng công thức riêng.
"""

from __future__ import annotations

from engine.can_chi import CAN_HANH, CAN_NAMES, CHI_HANH, CHI_NAMES
from engine.cuong_nhuoc import _seasonal_bonus
from engine.hoa_hop import detect_stem_transformations, effective_stem_hanh
from engine.tang_can import get_tang_can

RULE_VERSION = "2026-10.1"

# ─────────────────────────────────────────────────────────────────────────────
# Hằng (đặc tả mục 3–6). So ngưỡng trên giá trị CHƯA làm tròn.
# ─────────────────────────────────────────────────────────────────────────────

NGUONG_VUONG = 0.55
NGUONG_NHUOC = 0.40
NGUONG_CUC_VUONG = 0.70
NGUONG_NGHIENG = 0.50          # 6.3.3: r < 0,50 nghiêng nhược, còn lại nghiêng vượng
TQ_TY_LE_MIN = 0.30
TQ_LECH_MAX = 0.15
VANG = 1.0                     # L < 1,0: hành không thành khí (điều hậu vắng, dụng vắng)
GOC_MIN = 0.6                  # tàng can ≥ 0,6 (chủ/trung khí) mới là gốc

HANH = ("Mộc", "Hỏa", "Thổ", "Kim", "Thủy")   # thứ tự vòng sinh, cũng là thứ tự hoà ở 6.3.2
_IDX = {h: i for i, h in enumerate(HANH)}
TRU = ("year", "month", "day", "hour")
_TRU_KHONG_GIO = ("year", "month", "day")


def me(h: str) -> str:
    """Hành sinh ``h``."""
    return HANH[(_IDX[h] - 1) % 5]


def con(h: str) -> str:
    """Hành ``h`` sinh."""
    return HANH[(_IDX[h] + 1) % 5]


def khac(h: str) -> str:
    """Hành khắc ``h``."""
    return HANH[(_IDX[h] - 2) % 5]


def bi_khac(h: str) -> str:
    """Hành ``h`` khắc."""
    return HANH[(_IDX[h] + 2) % 5]


def nhom_hanh(dm: str) -> dict[str, str]:
    """Năm nhóm thập thần → hành, theo hành nhật chủ."""
    return {"TK": dm, "AN": me(dm), "TT": con(dm), "TAI": bi_khac(dm), "QS": khac(dm)}


def _chi(*ten: str) -> frozenset[int]:
    return frozenset(CHI_NAMES.index(t) for t in ten)


# 5.1 — mùa của nhật chủ; tam hội, tam hợp; chữ phá cách (TLMC-NC, nguyên văn)
MUA = {
    "Mộc": _chi("Dần", "Mão", "Thìn"), "Hỏa": _chi("Tỵ", "Ngọ", "Mùi"),
    "Kim": _chi("Thân", "Dậu", "Tuất"), "Thủy": _chi("Hợi", "Tý", "Sửu"),
    "Thổ": _chi("Thìn", "Tuất", "Sửu", "Mùi"),
}
TAM_HOI = {
    "Mộc": _chi("Dần", "Mão", "Thìn"), "Hỏa": _chi("Tỵ", "Ngọ", "Mùi"),
    "Kim": _chi("Thân", "Dậu", "Tuất"), "Thủy": _chi("Hợi", "Tý", "Sửu"),
}
TAM_HOP = {
    "Mộc": _chi("Hợi", "Mão", "Mùi"), "Hỏa": _chi("Dần", "Ngọ", "Tuất"),
    "Kim": _chi("Tỵ", "Dậu", "Sửu"), "Thủy": _chi("Thân", "Tý", "Thìn"),
}
CAM_NHAT_HANH = {                       # DM → (hành can cấm, chi cấm)
    "Mộc": ("Kim", _chi("Thân", "Dậu")),      # 無庚辛申酉
    "Hỏa": ("Thủy", _chi("Hợi", "Tý")),       # 無壬癸亥子
    "Thổ": ("Mộc", _chi("Dần", "Mão")),       # 無甲乙寅卯
    "Kim": ("Hỏa", _chi("Ngọ", "Mùi")),       # 無丙丁午未
    "Thủy": ("Thổ", _chi("Mùi", "Tuất")),     # 無戊己未戌
}

# 5.2 — cặp ngũ hợp, hoá thần, tháng hợp lệ (TLMC-NC)
HOA = (
    (frozenset({"Giáp", "Kỷ"}), "Thổ", _chi("Thìn", "Tuất", "Sửu", "Mùi")),
    (frozenset({"Ất", "Canh"}), "Kim", _chi("Tỵ", "Dậu", "Sửu", "Thân")),
    (frozenset({"Bính", "Tân"}), "Thủy", _chi("Thân", "Tý", "Thìn", "Hợi")),
    (frozenset({"Đinh", "Nhâm"}), "Mộc", _chi("Hợi", "Mão", "Mùi", "Dần")),
    (frozenset({"Mậu", "Quý"}), "Hỏa", _chi("Dần", "Ngọ", "Tuất", "Tỵ")),
)
_CHI_KHONG_PHA_HOA_THUY = _chi("Thìn", "Sửu")   # 辰丑皆潤土，不以克破論

# 6.3.1 — tháng cần điều hậu (LCDU)
THANG_HAN = _chi("Tý", "Sửu", "Dần")
THANG_NHIET = _chi("Tỵ", "Ngọ", "Mùi")
HANH_DIEU_HAU = {"HAN": "Hỏa", "NHIET": "Thủy"}

# Thứ tự hoà (đặc tả, [Quy ước])
THU_TU_NGUYEN_NHAN_NHUOC = ("QS", "TT", "TAI")   # 6.1
THU_TU_TONG = ("QS", "TAI", "TT")                # 5.3

# ─────────────────────────────────────────────────────────────────────────────
# Bảng vai. Một dòng = (dụng, hỷ theo thứ tự nguồn, kỵ, cừu theo thứ tự nguồn).
# Hành không có trong dòng là Nhàn.
# ─────────────────────────────────────────────────────────────────────────────

BANG_NHOM: dict[str, tuple[str, tuple[str, ...], str, tuple[str, ...]]] = {
    "N-QS": ("AN", ("TK",), "QS", ("TAI",)),                  # 6.1
    "N-TAI": ("TK", ("AN",), "TAI", ("QS", "TT")),
    "N-TT": ("AN", ("TK", "QS"), "TT", ("TAI",)),
    "V-AN": ("TAI", ("TT",), "AN", ("TK",)),                  # 6.2
    "V-TK-QS": ("QS", ("TAI",), "TK", ("AN",)),
    "V-TK-TT": ("TT", ("TAI",), "TK", ("AN",)),
    "DB-NHAT-HANH": ("TK", ("AN", "TT"), "QS", ()),           # 5.1
    "DB-TONG-TAI": ("TAI", ("TT",), "TK", ("AN",)),           # 5.3
    "DB-TONG-SAT": ("QS", ("TAI",), "AN", ("TK", "TT")),
    "DB-TONG-NHI": ("TT", ("TAI", "TK"), "AN", ("QS",)),
    "DB-TONG-VUONG": ("TK", ("AN",), "QS", ("TAI",)),         # 5.4
    "DB-TONG-CUONG": ("TK", ("AN",), "QS", ("TAI", "TT")),
}
BANG_DIEU_HAU: dict[str, tuple[str, tuple[str, ...], str, tuple[str, ...]]] = {
    "CB-DH-HAN": ("Hỏa", ("Mộc",), "Thủy", ("Kim",)),        # 6.3.1
    "CB-DH-NHIET": ("Thủy", ("Kim",), "Hỏa", ("Mộc",)),
}


def vai_hoa(than: str) -> tuple[str, tuple[str, ...], str, tuple[str, ...]]:
    """5.2: dòng vai của hoá khí theo hoá thần H (nhàn là hành H khắc)."""
    return than, (me(than), con(than)), khac(than), ()


def vai_thong_quan(manh: str) -> tuple[str, tuple[str, ...], str, tuple[str, ...]]:
    """6.3.2: M khắc Y; dụng là hành M sinh, hỷ rỗng, nhàn là M và Y."""
    cau = con(manh)
    return cau, (), khac(cau), (khac(manh),)


_CHINH_CACH = ("N-QS", "N-TAI", "N-TT", "V-AN", "V-TK-QS", "V-TK-TT")
NHANH_HOP_LE = frozenset(
    set(_CHINH_CACH)
    | {"CB-N-QS", "CB-N-TAI", "CB-N-TT", "CB-V-AN", "CB-V-TK-QS"}   # CB-V-TK-TT không thể: r < 0,55 < 0,70
    | set(BANG_DIEU_HAU) | {"CB-TQ"}
    | {"DB-NHAT-HANH", "DB-HOA", "DB-TONG-TAI", "DB-TONG-SAT", "DB-TONG-NHI",
       "DB-TONG-VUONG", "DB-TONG-CUONG"}
)
assert len(NHANH_HOP_LE) == 21

# 8.4: ô đơn được rỗng ở đúng ba cặp (ô, nhánh). Ngoài ra rỗng là lỗi phép tính.
VAI_RONG_HOP_LE = frozenset({("hi_than", "CB-TQ"), ("cuu_than", "DB-NHAT-HANH"), ("cuu_than", "DB-HOA")})

VAI_TEN = ("Dụng", "Hỉ", "Kỵ", "Cừu", "Nhàn")


# ─────────────────────────────────────────────────────────────────────────────
# Lực (đặc tả mục 3, đúng cách engine đếm — ENG §21)
# ─────────────────────────────────────────────────────────────────────────────

def _tru_dung(tu_tru: dict, co_gio: bool) -> tuple[str, ...]:
    """B0: kiểm đầu vào; thiếu dữ liệu bắt buộc là lỗi, không đoán."""
    tru = TRU if co_gio else _TRU_KHONG_GIO
    for p in tru:
        tru_p = tu_tru.get(p) if isinstance(tu_tru, dict) else None
        if not isinstance(tru_p, dict):
            raise ValueError(f"dung_than 2026-10.1: thiếu trụ {p!r}"
                             + (" (không có giờ thì gọi co_gio=False)" if p == "hour" else ""))
        can, chi = tru_p.get("can_idx"), tru_p.get("chi_idx")
        if not (isinstance(can, int) and 0 <= can < 10 and isinstance(chi, int) and 0 <= chi < 12):
            raise ValueError(f"dung_than 2026-10.1: trụ {p!r} sai can_idx/chi_idx")
    return tru


def _hop_hoa(tu_tru: dict, co_gio: bool) -> list[dict]:
    """Cặp can hợp hoá của engine; thiếu giờ thì bỏ mọi cặp có trụ giờ (mục 7)."""
    if co_gio:
        return detect_stem_transformations(tu_tru)
    # Mỗi cặp kề được engine xét độc lập; trụ giờ giả mang đúng can ngày thì cặp ngày–giờ
    # tự bị bỏ (cùng can không hợp), hai cặp kia không đổi.
    gia = {p: tu_tru[p] for p in _TRU_KHONG_GIO}
    gia["hour"] = {"can_idx": tu_tru["day"]["can_idx"], "chi_idx": tu_tru["day"]["chi_idx"]}
    return [t for t in detect_stem_transformations(gia) if "hour" not in (t["pillar_a"], t["pillar_b"])]


def _can_hieu_luc(tu_tru: dict, tru: tuple[str, ...], hh: list[dict]) -> dict[str, str]:
    """Hành thiên can sau hợp hoá, theo trụ."""
    ra = {}
    for p in tru:
        ci = tu_tru[p]["can_idx"]
        eh, da_hoa = effective_stem_hanh(p, ci, hh)
        ra[p] = eh if da_hoa else CAN_HANH[ci]
    return ra


def _dem(tu_tru: dict, tru: tuple[str, ...], can_hl: dict[str, str], g: dict[str, str]):
    """L[hành] (mọi can kể cả can ngày + tàng can) và W[nhóm] (không tính can ngày)."""
    nhom_cua = {h: k for k, h in g.items()}
    L = {h: 0.0 for h in HANH}
    W = {k: 0.0 for k in g}
    for p in tru:
        L[can_hl[p]] += 1.0
        if p != "day":
            W[nhom_cua[can_hl[p]]] += 1.0
        for an in get_tang_can(tu_tru[p]["chi_idx"]):
            L[an["hanh"]] += an["weight"]
            W[nhom_cua[an["hanh"]]] += an["weight"]
    return L, W


def _ty_le(dm: str, L: dict[str, float], thang: int) -> float:
    ho = L[dm] + L[me(dm)]
    chong = sum(L.values()) - ho
    b = _seasonal_bonus(dm, thang)
    ho += max(0, b)
    chong += max(0, -b)
    return ho / (ho + chong) if ho + chong else 0.5


def luc(tu_tru: dict, co_gio: bool = True) -> dict:
    """L, W, r của đúng các trụ được dùng (đặc tả mục 3; thiếu giờ: ba trụ)."""
    tru = _tru_dung(tu_tru, co_gio)
    hh = _hop_hoa(tu_tru, co_gio)
    dm = CAN_HANH[tu_tru["day"]["can_idx"]]
    g = nhom_hanh(dm)
    can_hl = _can_hieu_luc(tu_tru, tru, hh)
    L, W = _dem(tu_tru, tru, can_hl, g)
    return {"dm": dm, "g": g, "L": L, "W": W, "r": _ty_le(dm, L, tu_tru["month"]["chi_idx"]),
            "can_hl": can_hl, "tru": tru}


# ─────────────────────────────────────────────────────────────────────────────
# Cách đặc biệt (mục 5) — chỉ xét khi có giờ
# ─────────────────────────────────────────────────────────────────────────────

def _so(x: float) -> str:
    return f"{x:.1f}"


def _ten_can(tu_tru: dict, p: str) -> str:
    return CAN_NAMES[tu_tru[p]["can_idx"]]


def _hop_can_ngay(tu_tru: dict, p: str) -> bool:
    """Can ở tháng/giờ ngũ hợp với can ngày (TLMC: «與日干丁火作合» thì không tính)."""
    if p not in ("month", "hour"):
        return False
    cap = frozenset({_ten_can(tu_tru, p), _ten_can(tu_tru, "day")})
    return any(cap == c for c, _h, _t in HOA)


def _nhat_hanh(tu_tru: dict, dm: str, chis: list[int], thang: int, can_hl: dict) -> str | None:
    """5.1. Trả mã cục khi thành cách, None khi không."""
    if thang not in MUA[dm]:
        return None
    hanh_cam, chi_cam = CAM_NHAT_HANH[dm]
    if any(can_hl[p] == hanh_cam and not _hop_can_ngay(tu_tru, p) for p in TRU if p != "day"):
        return None
    if any(c in chi_cam for c in chis):
        return None
    co = set(chis)
    if dm == "Thổ":
        if MUA["Thổ"] <= co:
            return "TU_KHO"
        # «四柱純土»: can ngày là chính nhật chủ Thổ, nên chỉ xét ba can kia (hành hiệu lực)
        if all(CHI_HANH[c] == "Thổ" for c in chis) and all(can_hl[p] == "Thổ" for p in TRU if p != "day"):
            return "THUAN_THO"
        return None
    if TAM_HOI[dm] <= co:
        return "TAM_HOI"
    if TAM_HOP[dm] <= co:
        return "TAM_HOP"
    return None


def _hoa_khi(tu_tru: dict, thang: int, can_hl: dict) -> tuple[str, str] | None:
    """5.2 (đã biết r ≤ 0,40). Trả (hoá thần, trụ của can hợp) khi thành cách."""
    ngay = _ten_can(tu_tru, "day")
    for cap, than, thang_hop_le in HOA:
        if ngay not in cap or thang not in thang_hop_le:
            continue
        doi = next(iter(cap - {ngay}))
        o = [p for p in ("year", "month", "hour") if _ten_can(tu_tru, p) == doi]
        if len(o) != 1 or o[0] == "year":            # 在年幹不是; hai can hợp là đố hợp
            continue
        if o[0] == "month" and _ten_can(tu_tru, "year") == ngay:
            continue                                  # đố hợp: hai can ngày tranh can tháng
        pha = khac(than)
        if any(can_hl[p] == pha for p in TRU if p not in ("day", o[0])):
            continue                                  # 化X不見[khắc X]
        # 因化而破: cặp can kề khác (không chứa trụ ngày, tức năm–tháng) hoá thành hành phá
        cap_nt = frozenset({_ten_can(tu_tru, "year"), _ten_can(tu_tru, "month")})
        if any(cap_nt == c2 and thang in t2 and h2 == pha for c2, h2, t2 in HOA):
            continue
        if any(get_tang_can(tu_tru[p]["chi_idx"])[0]["hanh"] == pha
               and not (than == "Thủy" and tu_tru[p]["chi_idx"] in _CHI_KHONG_PHA_HOA_THUY)
               for p in TRU):
            continue                                  # chủ khí của chi là hành phá
        return than, o[0]
    return None


def _cuc_tron(chis: list[int]) -> dict[int, str]:
    """chi_idx → hành của cục trọn vẹn (tam hội, rồi tam hợp) chứa nó."""
    co, ra = set(chis), {}
    for bang in (TAM_HOI, TAM_HOP):
        for h, bo in bang.items():
            if bo <= co:
                for c in bo:
                    ra[c] = h
    return ra


def _co_goc(tu_tru: dict, tru: tuple[str, ...], hanh: set[str], cuc: dict[int, str]) -> bool:
    """Có tàng can ≥ 0,6 mang hành trong ``hanh`` ở một chi chưa nhập cục của hành khác."""
    for p in tru:
        c = tu_tru[p]["chi_idx"]
        if c in cuc and cuc[c] not in hanh:
            continue
        if any(an["hanh"] in hanh and an["weight"] >= GOC_MIN for an in get_tang_can(c)):
            return True
    return False


def _lon_nhat(W: dict[str, float], thu_tu: tuple[str, ...]) -> str:
    """Nhóm W lớn nhất; hoà thì nhóm đứng trước trong ``thu_tu``."""
    return max(thu_tu, key=lambda k: W[k])


def _so_sanh(W: dict[str, float], a: str, b: str) -> str:
    return f"{a}:{_so(W[a])}{'>' if W[a] > W[b] else '='}{b}:{_so(W[b])}"


def _dac_biet(tu_tru: dict, lc: dict) -> tuple[str, tuple, list[str]] | None:
    dm, g, L, W, r, can_hl, tru = (lc[k] for k in ("dm", "g", "L", "W", "r", "can_hl", "tru"))
    thang = tu_tru["month"]["chi_idx"]
    ten_thang = f"thang={CHI_NAMES[thang]}"
    chis = [tu_tru[p]["chi_idx"] for p in tru]

    cuc_nh = _nhat_hanh(tu_tru, dm, chis, thang, can_hl)
    if cuc_nh:
        return "DB-NHAT-HANH", BANG_NHOM["DB-NHAT-HANH"], [
            f"nhat_hanh={dm}", ten_thang, f"cuc={cuc_nh}", "khong_chu_pha"]

    if r <= NGUONG_NHUOC:
        hk = _hoa_khi(tu_tru, thang, can_hl)
        if hk:
            than, o = hk
            return "DB-HOA", vai_hoa(than), [
                f"hoa={_ten_can(tu_tru, 'day')}-{_ten_can(tu_tru, o)}@{o}:{than}", ten_thang, "khong_hanh_pha"]
        khong_an_can = all(can_hl[p] != g["AN"] for p in TRU if p != "day")
        if khong_an_can and not _co_goc(tu_tru, tru, {g["TK"], g["AN"]}, _cuc_tron(chis)):
            theo = _lon_nhat(W, THU_TU_TONG)
            if CHI_HANH[thang] == g[theo]:
                ten = {"QS": "DB-TONG-SAT", "TAI": "DB-TONG-TAI", "TT": "DB-TONG-NHI"}[theo]
                return ten, BANG_NHOM[ten], [
                    f"tong={theo}:{_so(W[theo])}", ten_thang, "khong_an_can", "khong_goc"]

    khong_tai_quan = (all(can_hl[p] not in (g["QS"], g["TAI"]) for p in TRU if p != "day")
                      and not _co_goc(tu_tru, tru, {g["QS"], g["TAI"]}, {}))
    if khong_tai_quan and CHI_HANH[thang] in (g["TK"], g["AN"]) and r >= NGUONG_VUONG:
        vuong = W["AN"] < W["TK"] / 2
        ten = "DB-TONG-VUONG" if vuong else "DB-TONG-CUONG"
        return ten, BANG_NHOM[ten], [
            ten_thang, "khong_tai_quan",
            f"AN:{_so(W['AN'])}{'<' if vuong else '>='}TK/2:{W['TK'] / 2:.2f}"]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Chính cách (mục 6)
# ─────────────────────────────────────────────────────────────────────────────

def _dieu_hau(L: dict[str, float], thang: int) -> str | None:
    """6.3.1: đủ ba điều kiện thì trả "HAN" / "NHIET"."""
    lanh, am = L["Kim"] + L["Thủy"], L["Mộc"] + L["Hỏa"]
    if thang in THANG_HAN and L["Hỏa"] < VANG and lanh > am:
        return "HAN"
    if thang in THANG_NHIET and L["Thủy"] < VANG and am > lanh:
        return "NHIET"
    return None


def _phu_uc(W: dict[str, float], r: float, nghieng: str) -> tuple[str, list[str]]:
    """Bảng 6.1 (nghieng="N") hoặc 6.2 (nghieng="V") theo nguyên nhân."""
    if nghieng == "N":
        nn = _lon_nhat(W, THU_TU_NGUYEN_NHAN_NHUOC)
        nhi = _lon_nhat(W, tuple(k for k in THU_TU_NGUYEN_NHAN_NHUOC if k != nn))
        return f"N-{nn}", [f"nguyen_nhan={_so_sanh(W, nn, nhi)}"]
    if W["AN"] > W["TK"]:
        return "V-AN", [f"nguyen_nhan={_so_sanh(W, 'AN', 'TK')}"]
    ly = [f"nguyen_nhan={_so_sanh(W, 'TK', 'AN')}"]
    if r >= NGUONG_CUC_VUONG:
        return "V-TK-TT", ly + ["cuc_vuong"]
    return "V-TK-QS", ly + ["khong_cuc_vuong"]


def _thong_quan(L: dict[str, float]) -> tuple[str, list[str]] | None:
    """6.3.2: trả (hành khắc M, lý do) khi hai hành lớn nhất khắc nhau và cân sức."""
    xep = sorted(HANH, key=lambda h: -L[h])        # sắp ổn định: hoà theo thứ tự HANH
    a, b = xep[0], xep[1]
    if khac(b) == a:
        manh, yeu = a, b
    elif khac(a) == b:
        manh, yeu = b, a
    else:
        return None
    tong = sum(L.values())
    if L[a] >= TQ_TY_LE_MIN * tong and L[b] >= TQ_TY_LE_MIN * tong and L[a] - L[b] <= TQ_LECH_MAX * L[a]:
        return manh, [f"thong_quan={manh}_khac_{yeu}:{_so(L[manh])}/{_so(L[yeu])}"]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Dựng đầu ra (mục 8.1) và tính
# ─────────────────────────────────────────────────────────────────────────────

def _dong(nhanh: str, dong: tuple, g: dict[str, str] | None) -> dict:
    """Một dòng bảng → bốn ô đơn, ba tập, vai_5_hanh. ``g`` là None khi dòng đã ghi bằng hành."""
    dung, hy, ky, cuu = dong
    if g is not None:
        dung, hy, ky, cuu = g[dung], tuple(g[x] for x in hy), g[ky], tuple(g[x] for x in cuu)
    vai = {h: "Nhàn" for h in HANH}
    for h in cuu:
        vai[h] = "Cừu"
    vai[ky] = "Kỵ"
    for h in hy:
        vai[h] = "Hỉ"
    vai[dung] = "Dụng"
    return {
        "nhanh": nhanh,
        "dung_than": dung,
        "hi_than": hy[0] if hy else None,
        "ky_than": ky,
        "cuu_than": cuu[0] if cuu else None,
        "hy_tap": list(hy),
        "ky_tap": [ky, *cuu],
        "nhan_tap": [h for h in HANH if vai[h] == "Nhàn"],
        "vai_5_hanh": vai,
    }


def _cuong_nhuoc(r: float) -> str:
    if r >= NGUONG_VUONG:
        return "vượng"
    if r <= NGUONG_NHUOC:
        return "nhược"
    return "cân bằng"


def tinh(tu_tru: dict, co_gio: bool = True) -> dict:
    """
    Bộ vai ``2026-10.1`` của một lá số (đặc tả mục 4: B0 → B1 → B2 → B3).

    Args:
        tu_tru: dict của ``get_tu_tru`` (chỉ đọc ``can_idx``/``chi_idx`` các trụ).
        co_gio: False = khách không khai giờ: tính ba trụ, không xét cách đặc biệt (mục 7);
            khi ấy ``tu_tru`` không cần trụ giờ, có thì bị bỏ qua.

    Returns: các trường của đặc tả 8.1.
    """
    lc = luc(tu_tru, co_gio)
    g, L, W, r = lc["g"], lc["L"], lc["W"], lc["r"]
    thang = tu_tru["month"]["chi_idx"]
    ly_do = [f"r={r:.3f}"]
    co: dict = {"ty_le": round(r, 3), "thieu_gio": not co_gio}

    db = _dac_biet(tu_tru, lc) if co_gio else None
    if not co_gio:
        ly_do.append("thieu_gio")
    dh = _dieu_hau(L, thang)

    if db:
        nhanh, dong, ly = db
        kq = _dong(nhanh, dong, None if nhanh == "DB-HOA" else g)
        ly_do += ly
    elif r >= NGUONG_VUONG or r <= NGUONG_NHUOC:
        nhanh, ly = _phu_uc(W, r, "V" if r >= NGUONG_VUONG else "N")
        kq = _dong(nhanh, BANG_NHOM[nhanh], g)
        ly_do += ly
        if dh:                                         # 6.4: ghi nhận, không đổi dụng
            h = HANH_DIEU_HAU[dh]
            vai = kq["vai_5_hanh"][h]
            if vai == "Nhàn":
                kq["vai_5_hanh"][h] = "Hỉ"
                kq["hy_tap"].append(h)
                kq["nhan_tap"].remove(h)
            co["dieu_hau"] = f"{dh}:{vai}"
            ly_do.append(f"dieu_hau={dh}:{vai}")
        else:
            ly_do.append("khong_dieu_hau")
    elif dh:
        nhanh = f"CB-DH-{dh}"
        kq = _dong(nhanh, BANG_DIEU_HAU[nhanh], None)
        h = HANH_DIEU_HAU[dh]
        lanh, am = _so(L["Kim"] + L["Thủy"]), _so(L["Mộc"] + L["Hỏa"])
        ly_do += [f"dieu_hau={dh}", f"thang={CHI_NAMES[thang]}", f"{h}:{_so(L[h])}<{_so(VANG)}",
                  f"Kim+Thủy:{lanh}>Mộc+Hỏa:{am}" if dh == "HAN" else f"Mộc+Hỏa:{am}>Kim+Thủy:{lanh}"]
    else:
        tq = _thong_quan(L)
        if tq:
            manh, ly = tq
            kq = _dong("CB-TQ", vai_thong_quan(manh), None)
            ly_do += ["khong_dieu_hau"] + ly
        else:
            goc, ly = _phu_uc(W, r, "N" if r < NGUONG_NGHIENG else "V")
            kq = _dong(f"CB-{goc}", BANG_NHOM[goc], g)
            ly_do += ly + ["khong_dieu_hau", "khong_thong_quan"]

    co["dung_vang"] = L[kq["dung_than"]] < VANG
    return {
        "rule_version": RULE_VERSION,
        **kq,
        "cuong_nhuoc": _cuong_nhuoc(r),
        "co": co,
        "ly_do": ly_do,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Bất biến (mục 9.1–9.5, và 9.6 trong phạm vi engine: rule_version)
# ─────────────────────────────────────────────────────────────────────────────

def _dong_ky_vong(kq: dict) -> tuple | None:
    """Dòng bảng của nhánh, suy lại từ chính đầu ra (nhật chủ suy từ dụng), sau điều chỉnh 6.4."""
    nhanh, dung = kq["nhanh"], kq["dung_than"]
    if nhanh in BANG_DIEU_HAU:
        return BANG_DIEU_HAU[nhanh]
    if nhanh == "DB-HOA":
        return vai_hoa(dung)
    if nhanh == "CB-TQ":
        return vai_thong_quan(me(dung))
    goc = nhanh[3:] if nhanh.startswith(("CB-N-", "CB-V-")) else nhanh
    if goc not in BANG_NHOM:
        return None
    dong = BANG_NHOM[goc]
    dm = next(h for h in HANH if nhom_hanh(h)[dong[0]] == dung)
    g = nhom_hanh(dm)
    hy = [g[x] for x in dong[1]]
    dh = (kq.get("co") or {}).get("dieu_hau")
    if dh and nhanh in _CHINH_CACH and dh.endswith(":Nhàn"):
        hy.append(HANH_DIEU_HAU[dh.split(":")[0]])
    return g[dong[0]], tuple(hy), g[dong[2]], tuple(g[x] for x in dong[3])


def kiem_bat_bien(kq: dict) -> list[str]:
    """Bất biến 9.1–9.5 (và phiên bản). Danh sách rỗng là đạt."""
    loi: list[str] = []
    try:
        vai = kq["vai_5_hanh"]
        o = {k: kq[k] for k in ("dung_than", "hi_than", "ky_than", "cuu_than")}
        tap = {k: kq[k] for k in ("hy_tap", "ky_tap", "nhan_tap")}
        nhanh = kq["nhanh"]
    except (KeyError, TypeError) as e:
        return [f"thiếu trường: {e}"]

    if kq.get("rule_version") != RULE_VERSION:
        loi.append("9.6: rule_version không phải 2026-10.1")
    # 9.1
    if not isinstance(vai, dict) or set(vai) != set(HANH):
        return loi + ["9.1: vai_5_hanh không đủ năm hành"]
    if any(v not in VAI_TEN for v in vai.values()):
        loi.append("9.1: vai lạ trong vai_5_hanh")
    if list(vai.values()).count("Dụng") != 1:
        loi.append("9.1: không đúng một Dụng")
    # ô rỗng (8.4)
    for k in ("dung_than", "ky_than"):
        if o[k] not in HANH:
            loi.append(f"8.1: {k} rỗng hoặc sai")
    for k in ("hi_than", "cuu_than"):
        if o[k] is None:
            if (k, nhanh) not in VAI_RONG_HOP_LE:
                loi.append(f"8.4: {k} rỗng ngoài VAI_RONG_HOP_LE")
        elif o[k] not in HANH:
            loi.append(f"8.1: {k} sai")
        elif (k, nhanh) in VAI_RONG_HOP_LE:
            loi.append(f"8.4: {k} phải rỗng ở {nhanh}")
    if loi and any(x.startswith("8.1") for x in loi):
        return loi
    # 9.2
    for k, ten in (("dung_than", "Dụng"), ("ky_than", "Kỵ"), ("hi_than", "Hỉ"), ("cuu_than", "Cừu")):
        if o[k] is not None and vai[o[k]] != ten:
            loi.append(f"9.2: vai_5_hanh[{k}] không phải {ten}")
    # 9.3
    don = [x for x in o.values() if x is not None]
    if len(set(don)) != len(don):
        loi.append("9.3: bốn ô đơn trùng nhau")
    # 9.4
    bo = [set(tap["hy_tap"]), set(tap["ky_tap"]), set(tap["nhan_tap"]), {o["dung_than"]}]
    if any(len(tap[k]) != len(set(tap[k])) for k in tap):
        loi.append("9.4: phần tử lặp trong một tập")
    if any(a & b for i, a in enumerate(bo) for b in bo[i + 1:]):
        loi.append("9.4: các tập giao nhau")
    if set().union(*bo) != set(HANH):
        loi.append("9.4: hợp các tập không đủ năm hành")
    tu_tap = {h: "Nhàn" for h in HANH}
    tu_tap.update({h: "Cừu" for h in tap["ky_tap"][1:]})
    tu_tap.update({h: "Kỵ" for h in tap["ky_tap"][:1]})
    tu_tap.update({h: "Hỉ" for h in tap["hy_tap"]})
    tu_tap[o["dung_than"]] = "Dụng"
    if tu_tap != vai:
        loi.append("9.4: vai_5_hanh lệch ba tập")
    if tap["ky_tap"][:1] != [o["ky_than"]] or (tap["hy_tap"][:1] or [None])[0] != o["hi_than"] \
            or (tap["ky_tap"][1:2] or [None])[0] != o["cuu_than"]:
        loi.append("8.1: ô đơn không là phần tử đầu của tập")
    # 9.5
    if nhanh not in NHANH_HOP_LE:
        loi.append(f"9.5: nhánh {nhanh!r} ngoài 21 mã")
    else:
        dong = _dong_ky_vong(kq)
        if dong is None or (o["dung_than"], tuple(tap["hy_tap"]), o["ky_than"], tuple(tap["ky_tap"][1:])) != dong:
            loi.append("9.5: bộ vai lệch dòng bảng của nhánh")
    dh = (kq.get("co") or {}).get("dieu_hau")
    if dh is not None and nhanh not in _CHINH_CACH:
        loi.append("6.4: cờ dieu_hau ngoài nhánh vượng/nhược")
    return loi
