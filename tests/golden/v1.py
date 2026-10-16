"""Bộ golden v1: đầu ra của `main` (88b7a66) TRƯỚC khi cài luật `2026-10.1`.

Mục đích: nghiệm thu "các bên không yêu cầu luật mới vẫn giữ nguyên hành vi v1".
Hai tệp dữ liệu nằm cạnh tệp này:

- ``v1_http.json``: 104 lời gọi. 88 lời gọi thành công phủ sáu route các site
  đang dùng (``/v1/la-so-full``, ``/v1/la-so``, ``/v1/la-so/luu-nien``,
  ``/v1/hop-tuoi``, ``/v1/phong-thuy``, ``/v1/chon-ngay``), payload chép khuôn mã
  site thật; 16 lời gọi v1 TỪ CHỐI (ngày sai, 29/02 năm không nhuận, năm < 1900,
  ngày tương lai, giờ/giới/năm/ý định/quan hệ sai, khoảng ngày sai), ghim mã
  trạng thái và thân lỗi. Ngày 16/10/2026 cả 104 lời gọi chạy trên production
  ``https://tu-tru-api.fly.dev`` và trùng 104/104 sau chuẩn hoá (báo cáo Task 2.0,
  repo nuoiconthuanmenh.vn).
- ``v1_find_dung_than.json``: đầu vào ``get_tu_tru`` và đầu ra ``find_dung_than``
  v1 của 60 lá số (``cases``) cộng 63 lá số chọn theo nhánh (``theo_nhanh``: ba lá
  số đầu tiên trong mẫu tổng hợp cho MỖI nhánh trong 21 nhánh của bản cài thử
  ``2026-10.1``; nhãn nhánh chỉ để phủ, tệp CHỈ lưu đầu ra v1), và vân tay của
  toàn bộ mẫu tổng hợp (``van_tay_mau``, 6.786 lá số, đặc tả mục 11: mỗi tuần một
  ngày 01/01/2005–31/08/2026 × khung giờ 2·6·10·14·18·22).

"Từng byte" ở mọi test golden nghĩa là từng byte của DẠNG CHÍNH TẮC
(``chuoi()``: ``json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"))``),
không phải của thân thô: thứ tự khoá trong phản hồi KHÔNG được canh (các site đọc
theo khoá), mọi thứ khác (giá trị, kiểu, độ dài và thứ tự danh sách, số thực theo
``repr``) được canh.

Chuẩn hoá bỏ ĐÚNG hai trường đổi theo thời điểm/máy gọi, không bỏ thêm:

- ``computed_at`` ở gốc thân: đồng hồ UTC lúc gọi (``api.version.utc_now_iso``).
- ``meta.share_token`` của chon-ngay: chữ ký HMAC theo ``SHARE_TOKEN_SECRET`` của
  máy chạy, cộng ``ts = int(time.time())``.

"Hôm nay" được đóng băng ở ``NGAY_DONG_BANG`` cho mọi chỗ engine đọc đồng hồ
để ra NGÀY (kiểm tra ngày sinh quá khứ, đại vận hiện hành), để golden không
trôi theo năm tháng. Danh sách chỗ đọc đồng hồ do
``test_clock_reads_are_all_frozen`` canh bằng AST.

Sinh lại (CHỈ khi cố ý đổi hành vi v1, và phải ghi lý do trong commit; sha256 của
hai tệp golden được ghim trong test nên sinh lại buộc phải sửa test):

    .venv/bin/python -m tests.golden.v1 --ghi
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FILE_HTTP = HERE / "v1_http.json"
FILE_DUNG = HERE / "v1_find_dung_than.json"

NGAY_DONG_BANG = "2026-10-16"

BO = (
    ("computed_at",),
    ("meta", "share_token"),
)

# (birth_date, slot, gender, name) — nhiều thập niên, giờ 0/23, 29/02, quanh Lập Xuân
HS = [
    ("06/05/1994", 8, 1, "Đỗ Minh Thái"),
    ("29/02/2024", 10, 1, "Nguyễn Gia Bảo"),
    ("29/02/2000", 23, -1, "Trần Thu Hà"),
    ("01/01/2025", 0, -1, "Lê Minh Anh"),
    ("31/12/2024", 23, 1, "Phạm Quốc Huy"),
    ("03/02/2026", 14, 1, "Võ Khánh Linh"),
    ("04/02/2026", 16, -1, "Hồ Ngọc Diệp"),
    ("15/06/1901", 11, 1, "Ngô Văn Cũ"),
    ("21/03/1990", 6, 1, "Bùi Văn Tâm"),
    ("12/08/1975", 18, -1, "Đặng Thị Lan"),
    ("09/09/1963", 20, 1, "Phan Văn Hùng"),
    ("25/12/1988", 22, -1, "Mai Thanh Thảo"),
    ("17/07/2019", 2, 1, "Đinh Gia Khang"),
    ("05/11/2010", 4, -1, "Lý Bảo Ngọc"),
    ("30/04/1955", 14, 1, "Trịnh Văn Lực"),
    ("19/06/2026", 10, 1, "Nguyễn Văn T"),
    ("08/03/2015", 16, -1, "Hoàng Mai Chi"),
    ("14/02/1984", 0, 1, "Cao Minh Đức"),
    ("28/02/2023", 18, -1, "Vũ An Nhiên"),
    ("01/03/2024", 8, 1, "Tạ Gia Huy"),
    ("10/10/2000", 11, -1, "Châu Ngọc Hân"),
    ("22/12/1999", 23, 1, "Lâm Tuấn Kiệt"),
    ("07/01/2026", 6, -1, "Dương Tuệ An"),
    ("16/09/2026", 20, 1, "Quách Minh Khôi"),
]

SLOTS = (0, 2, 4, 6, 8, 10, 11, 14, 16, 18, 20, 22, 23)

# Ba lá số ĐẦU TIÊN (theo thứ tự mẫu tổng hợp mục 11) của mỗi nhánh mà bản cài thử
# `2026-10.1` (docs/superpowers/specs/2026-10-14-dung-ky-ban-cai-thu.py, sha f849245b…,
# repo nuoiconthuanmenh.vn) gán, chạy trên engine 88b7a66 ngày 16/10/2026. Nhãn chỉ
# là ĐỘ PHỦ: lá số mà luật mới rẽ riêng (cách đặc biệt, tòng, điều hậu, thông quan)
# là chỗ một lỗi rò "luật mới chạy dù gọi v1" sẽ lộ ra. Golden chỉ lưu đầu ra v1.
LA_SO_THEO_NHANH = [
    ("2005-12-10", 2, "CB-DH-HAN"), ("2005-12-31", 2, "CB-DH-HAN"), ("2005-12-31", 14, "CB-DH-HAN"),
    ("2005-05-07", 14, "CB-DH-NHIET"), ("2005-05-14", 6, "CB-DH-NHIET"), ("2005-06-04", 2, "CB-DH-NHIET"),
    ("2005-01-01", 2, "CB-N-QS"), ("2005-01-01", 10, "CB-N-QS"), ("2005-01-08", 2, "CB-N-QS"),
    ("2005-01-15", 2, "CB-N-TAI"), ("2005-01-15", 18, "CB-N-TAI"), ("2005-01-22", 6, "CB-N-TAI"),
    ("2005-01-08", 6, "CB-N-TT"), ("2005-03-26", 10, "CB-N-TT"), ("2005-04-02", 2, "CB-N-TT"),
    ("2005-02-19", 14, "CB-TQ"), ("2005-03-12", 2, "CB-TQ"), ("2005-04-02", 22, "CB-TQ"),
    ("2005-01-01", 14, "CB-V-AN"), ("2005-01-15", 6, "CB-V-AN"), ("2005-01-29", 18, "CB-V-AN"),
    ("2005-01-15", 14, "CB-V-TK-QS"), ("2005-01-22", 14, "CB-V-TK-QS"), ("2005-01-29", 2, "CB-V-TK-QS"),
    ("2005-04-30", 10, "DB-HOA"), ("2005-08-20", 6, "DB-HOA"), ("2006-04-15", 10, "DB-HOA"),
    ("2007-02-03", 14, "DB-NHAT-HANH"), ("2009-02-28", 6, "DB-NHAT-HANH"), ("2009-09-12", 10, "DB-NHAT-HANH"),
    ("2007-02-10", 22, "DB-TONG-CUONG"), ("2007-03-31", 6, "DB-TONG-CUONG"), ("2007-03-31", 22, "DB-TONG-CUONG"),
    ("2006-10-14", 2, "DB-TONG-NHI"), ("2006-10-14", 18, "DB-TONG-NHI"), ("2006-11-04", 2, "DB-TONG-NHI"),
    ("2005-03-26", 22, "DB-TONG-SAT"), ("2005-10-08", 10, "DB-TONG-SAT"), ("2007-06-16", 14, "DB-TONG-SAT"),
    ("2008-10-04", 2, "DB-TONG-TAI"), ("2008-10-04", 18, "DB-TONG-TAI"), ("2008-10-04", 22, "DB-TONG-TAI"),
    ("2023-02-25", 6, "DB-TONG-VUONG"), ("2023-02-25", 22, "DB-TONG-VUONG"), ("2023-09-02", 22, "DB-TONG-VUONG"),
    ("2005-01-08", 14, "N-QS"), ("2005-01-29", 14, "N-QS"), ("2005-03-05", 6, "N-QS"),
    ("2005-01-29", 10, "N-TAI"), ("2005-02-19", 10, "N-TAI"), ("2005-04-23", 2, "N-TAI"),
    ("2005-01-08", 10, "N-TT"), ("2005-01-22", 2, "N-TT"), ("2005-01-22", 22, "N-TT"),
    ("2005-01-01", 22, "V-AN"), ("2005-02-05", 2, "V-AN"), ("2005-02-05", 6, "V-AN"),
    ("2005-01-01", 6, "V-TK-QS"), ("2005-01-01", 18, "V-TK-QS"), ("2005-01-15", 10, "V-TK-QS"),
    ("2005-04-16", 6, "V-TK-TT"), ("2005-04-16", 10, "V-TK-TT"), ("2005-04-16", 18, "V-TK-TT"),
]

# Số lá số mỗi nhánh của bản cài thử trên TOÀN mẫu tổng hợp (6.786), cùng lượt đo. Chỉ để
# ghi độ phủ của vân tay mẫu (nhánh hiếm nhất DB-TONG-VUONG có 5 lá số).
DEM_NHANH_MAU = {
    "CB-DH-HAN": 102, "CB-DH-NHIET": 90, "CB-N-QS": 539, "CB-N-TAI": 409, "CB-N-TT": 488,
    "CB-TQ": 113, "CB-V-AN": 380, "CB-V-TK-QS": 354, "DB-HOA": 57, "DB-NHAT-HANH": 37,
    "DB-TONG-CUONG": 23, "DB-TONG-NHI": 32, "DB-TONG-SAT": 14, "DB-TONG-TAI": 23,
    "DB-TONG-VUONG": 5, "N-QS": 779, "N-TAI": 646, "N-TT": 718, "V-AN": 900,
    "V-TK-QS": 870, "V-TK-TT": 207,
}


def tao_yeu_cau() -> list[dict]:
    ds: list[dict] = []

    def them(rid, method, path, params=None, body=None):
        ds.append({"id": rid, "method": method, "path": path, "params": params, "json": body})

    for i, (bd, bt, g, ten) in enumerate(HS):
        them(f"full-{i:02d}", "POST", "/v1/la-so-full",
             body={"birth_date": bd, "birth_time": bt, "gender": g, "name": ten,
                   "num_dai_van": 10, "num_luu_nien": 20, "format": "json"})
    them("full-vy-0", "POST", "/v1/la-so-full",
         body={"birth_date": "21/03/1990", "birth_time": 6, "gender": 1,
               "num_dai_van": 10, "num_luu_nien": 10, "view_year": 2026, "format": "json"})
    them("full-vy-1", "POST", "/v1/la-so-full",
         body={"birth_date": "29/02/2000", "birth_time": 10, "gender": 1,
               "num_dai_van": 8, "num_luu_nien": 12, "view_year": 2025, "format": "json"})

    for i in (0, 1, 2, 3, 4, 5, 6, 7, 9, 12, 13, 17, 19, 22):
        bd, bt, g, _ = HS[i]
        them(f"laso-{i:02d}", "GET", "/v1/la-so",
             params={"birth_date": bd, "birth_time": bt, "gender": g})
    for i in (8, 21):
        bd, bt, _, _ = HS[i]
        them(f"laso-ng-{i:02d}", "GET", "/v1/la-so", params={"birth_date": bd, "birth_time": bt})

    for k, (i, nam) in enumerate([(0, 2026), (1, 2025), (1, 2028), (2, 2026), (3, 2026),
                                  (5, 2027), (8, 2026), (9, 2024), (10, 2030),
                                  (12, 2026), (14, 2026), (20, 2027)]):
        bd, bt, g, _ = HS[i]
        them(f"ln-{k:02d}", "GET", "/v1/la-so/luu-nien",
             params={"birth_date": bd, "birth_time": bt, "gender": g, "year": nam})

    cap = [(0, 9, None), (1, 2, None), (8, 11, None),
           (0, 11, "PHU_THE"), (8, 9, "PHU_THE"), (2, 4, "PHU_THE"),
           (10, 14, "DOI_TAC"), (10, 14, "DONG_NGHIEP"), (10, 14, "SEP_NHAN_VIEN"),
           (17, 21, "PHU_THE")]
    for k, (a, b, qh) in enumerate(cap):
        ba, ta, ga, _ = HS[a]
        bb, tb, gb, _ = HS[b]
        body = {"person1_birth_date": ba, "person1_birth_time": ta, "person1_gender": ga,
                "person2_birth_date": bb, "person2_birth_time": tb, "person2_gender": gb}
        if qh:
            body["relationship_type"] = qh
        them(f"ht-{k:02d}", "POST", "/v1/hop-tuoi", body=body)

    for i in (0, 1, 2, 3, 5, 9, 13, 17):
        bd, bt, g, _ = HS[i]
        them(f"pt-{i:02d}", "GET", "/v1/phong-thuy",
             params={"birth_date": bd, "birth_time": bt, "gender": g})
    for i in (8, 11, 1):
        bd, _, g, _ = HS[i]
        them(f"pt-ng-{i:02d}", "GET", "/v1/phong-thuy", params={"birth_date": bd, "gender": g})
    for k, (i, nam) in enumerate([(0, 2026), (9, 2026), (0, 2025), (12, 2027)]):
        bd, bt, g, _ = HS[i]
        them(f"pt-y-{k}", "GET", "/v1/phong-thuy",
             params={"birth_date": bd, "birth_time": bt, "gender": g, "year": nam})
    them("pt-partner", "GET", "/v1/phong-thuy",
         params={"birth_date": HS[0][0], "birth_time": HS[0][1], "gender": HS[0][2],
                 "partner_birth_date": HS[9][0]})

    cua = [("17/10/2026", "14/01/2027"), ("15/01/2027", "14/04/2027")]
    for k, (i, yd, w) in enumerate([(0, "KHAI_TRUONG", 0), (0, "DAM_CUOI", 1),
                                    (1, "NHAP_TRACH", 0), (2, "XUAT_HANH", 1),
                                    (9, "KY_HOP_DONG", 0), (13, "DONG_THO", 1),
                                    (17, "CAU_TAI", 0), (3, "AN_HOI", 1)]):
        bd, bt, g, _ = HS[i]
        tu, den = cua[w]
        them(f"cn-{k:02d}", "POST", "/v1/chon-ngay",
             body={"birth_date": bd, "birth_time": bt, "gender": g, "intent": yd,
                   "range_start": tu, "range_end": den, "top_n": 4})
    ds.extend(tao_yeu_cau_loi())
    return ds


def tao_yeu_cau_loi() -> list[dict]:
    """16 lời gọi v1 TỪ CHỐI: ghim mã trạng thái và thân lỗi (site rẽ nhánh theo `status == "error"`)."""
    full = {"birth_time": 8, "gender": 1, "num_dai_van": 10, "num_luu_nien": 20, "format": "json"}
    cn = {"birth_date": "06/05/1994", "birth_time": 8, "gender": 1, "top_n": 4}
    ht = {"person1_birth_date": "06/05/1994", "person1_birth_time": 8, "person1_gender": 1,
          "person2_birth_date": "12/08/1975", "person2_birth_time": 18, "person2_gender": -1}
    yc = [
        ("err-00", "POST", "/v1/la-so-full", None, {**full, "birth_date": "31/02/2020"}),
        ("err-01", "POST", "/v1/la-so-full", None, {**full, "birth_date": "29/02/2023"}),
        ("err-02", "POST", "/v1/la-so-full", None, {**full, "birth_date": "15/06/1899"}),
        ("err-03", "POST", "/v1/la-so-full", None, {**full, "birth_date": "01/01/2027"}),
        ("err-04", "POST", "/v1/la-so-full", None, {**full, "birth_date": "06/05/1994", "birth_time": 7}),
        ("err-05", "GET", "/v1/la-so", {"birth_date": "29/02/2023", "birth_time": 8, "gender": 1}, None),
        ("err-06", "GET", "/v1/la-so", {"birth_date": "06/05/1994", "birth_time": 8, "gender": 2}, None),
        ("err-07", "GET", "/v1/la-so/luu-nien",
         {"birth_date": "06/05/1994", "birth_time": 8, "gender": 1, "year": 2101}, None),
        ("err-08", "GET", "/v1/la-so/luu-nien",
         {"birth_date": "29/02/2025", "birth_time": 8, "gender": 1, "year": 2026}, None),
        ("err-09", "POST", "/v1/hop-tuoi", None, {**ht, "relationship_type": "XYZ"}),
        ("err-10", "POST", "/v1/hop-tuoi", None, {**ht, "person1_birth_date": "29/02/2023"}),
        ("err-11", "GET", "/v1/phong-thuy", {"birth_date": "06/05/1994", "birth_time": 7, "gender": 1}, None),
        ("err-12", "GET", "/v1/phong-thuy",
         {"birth_date": "06/05/1994", "birth_time": 8, "gender": 1, "partner_birth_date": "30/02/2000"}, None),
        ("err-13", "POST", "/v1/chon-ngay", None,
         {**cn, "intent": "KHAI_TRUONG", "range_start": "17/10/2026", "range_end": "31/03/2027"}),
        ("err-14", "POST", "/v1/chon-ngay", None,
         {**cn, "intent": "KHONG_CO", "range_start": "17/10/2026", "range_end": "14/01/2027"}),
        ("err-15", "POST", "/v1/chon-ngay", None,
         {**cn, "intent": "KHAI_TRUONG", "range_start": "14/01/2027", "range_end": "17/10/2026"}),
    ]
    return [{"id": i, "method": m, "path": p, "params": q, "json": b} for i, m, p, q, b in yc]


def tao_la_so_dung() -> list[tuple[str, str, int]]:
    """60 lá số: 24 hồ sơ của bộ HTTP + 36 ngày trải 1931–2026 xoay vòng 13 khung giờ."""
    out = []
    for i, (bd, bt, _, _) in enumerate(HS):
        d, m, y = bd.split("/")
        out.append((f"hs-{i:02d}", f"{y}-{m}-{d}", bt))
    day = _dt.date(1931, 1, 7)
    for k in range(36):
        out.append((f"tg-{k:02d}", day.isoformat(), SLOTS[k % len(SLOTS)]))
        day += _dt.timedelta(days=977)
    return out


def mau_tong_hop():
    """Mẫu tổng hợp đặc tả mục 11: mỗi tuần một ngày 01/01/2005–31/08/2026 × giờ 2·6·10·14·18·22."""
    day, end = _dt.date(2005, 1, 1), _dt.date(2026, 8, 31)
    while day <= end:
        for hour in (2, 6, 10, 14, 18, 22):
            yield day.isoformat(), hour
        day += _dt.timedelta(days=7)


def van_tay_mau() -> dict:
    """sha256 của dòng chính tắc ``chuoi([iso, giờ, tu_tru, find_dung_than(tu_tru)])`` + "\\n"
    cho từng lá số của mẫu tổng hợp, nối theo thứ tự mẫu."""
    from engine.dung_than import find_dung_than
    from engine.pillars import get_tu_tru

    h, n = hashlib.sha256(), 0
    for iso, hour in mau_tong_hop():
        tt = get_tu_tru(iso, hour)
        tt_json = json.loads(json.dumps(tt))
        out = json.loads(json.dumps(find_dung_than(tt)))
        h.update((chuoi([iso, hour, tt_json, out]) + "\n").encode("utf-8"))
        n += 1
    return {"n": n, "sha256": h.hexdigest()}


def chuan_hoa(body):
    """Bỏ đúng các đường trong BO; không đụng gì khác."""
    if not isinstance(body, dict):
        return body
    body = json.loads(json.dumps(body))
    for duong in BO:
        cur = body
        for p in duong[:-1]:
            cur = cur.get(p) if isinstance(cur, dict) else None
        if isinstance(cur, dict):
            cur.pop(duong[-1], None)
    return body


def chuoi(x) -> str:
    """Dạng chuỗi chính tắc để so từng byte (thứ tự khoá không được canh, xem docstring module)."""
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha_tep(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dong_bang(dat, ngay_iso: str = NGAY_DONG_BANG) -> None:
    """Đóng băng 'hôm nay'. ``dat(obj, ten, gia_tri)`` = setattr hoặc monkeypatch.setattr."""
    y, m, d = map(int, ngay_iso.split("-"))
    co_dinh = _dt.date(y, m, d)

    class NgayDongBang(_dt.date):
        @classmethod
        def today(cls):
            return co_dinh

    import importlib

    import api.tz as tz

    def hom_nay(_tz=None):
        return co_dinh

    dat(tz, "today_in_tz", hom_nay)
    for ten in ("api.routes.la_so", "api.routes.la_so_luu_nien", "api.routes.la_so_full",
                "api.routes.tu_tru", "api.routes.hop_tuoi"):
        dat(importlib.import_module(ten), "date", NgayDongBang)
    for ten in ("api.routes.phong_thuy", "api.routes.weekly_summary"):
        dat(importlib.import_module(ten), "today_in_tz", hom_nay)
    import engine.dai_van as dv
    dat(dv, "dt_date", NgayDongBang)


def app_client():
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100000")
    from fastapi.testclient import TestClient

    from app import app

    return TestClient(app)


def goi(client, r: dict) -> dict:
    resp = client.request(r["method"], r["path"], params=r["params"], json=r["json"])
    return {"status": resp.status_code, "body": chuan_hoa(resp.json())}


def _dung_mot(rid, iso, slot, nhanh=None):
    from engine.dung_than import find_dung_than
    from engine.pillars import get_tu_tru

    tt = get_tu_tru(iso, slot)
    row = {"id": rid, "birth_date": iso, "birth_time": slot, "tu_tru": json.loads(json.dumps(tt)),
           "ket_qua": json.loads(json.dumps(find_dung_than(tt)))}
    if nhanh is not None:
        row["nhanh_ban_cai_thu"] = nhanh
    return row


def _ghi() -> None:
    dong_bang(setattr)
    client = app_client()
    ds = tao_yeu_cau()
    cases = [{**r, "ket_qua": goi(client, r)} for r in ds]
    FILE_HTTP.write_text(json.dumps(
        {"ngay_dong_bang": NGAY_DONG_BANG, "bo_khi_chuan_hoa": [".".join(p) for p in BO],
         "cases": cases}, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    rows = [_dung_mot(rid, iso, slot) for rid, iso, slot in tao_la_so_dung()]
    theo = [_dung_mot(f"nh-{nh}-{k % 3}", iso, slot, nh)
            for k, (iso, slot, nh) in enumerate(LA_SO_THEO_NHANH)]
    dem = {}
    for _, _, nh in LA_SO_THEO_NHANH:
        dem[nh] = dem.get(nh, 0) + 1
    FILE_DUNG.write_text(json.dumps(
        {"cases": rows, "theo_nhanh": theo, "dem_theo_nhanh": dem,
         "dem_nhanh_mau_tong_hop": DEM_NHANH_MAU, "van_tay_mau": van_tay_mau()},
        ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"ghi {len(cases)} ca HTTP → {FILE_HTTP} ({sha_tep(FILE_HTTP)})")
    print(f"ghi {len(rows)} + {len(theo)} lá số + vân tay mẫu → {FILE_DUNG} ({sha_tep(FILE_DUNG)})")


if __name__ == "__main__":
    if "--ghi" not in sys.argv:
        sys.exit("Chỉ ghi khi có --ghi (golden là hành vi v1 đã chốt).")
    _ghi()
