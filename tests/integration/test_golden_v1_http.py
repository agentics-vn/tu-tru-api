"""Golden v1 qua HTTP: lời gọi không yêu cầu luật mới phải trả y hệt `main` 88b7a66.

Dữ liệu và cách chuẩn hoá: xem ``tests/golden/v1.py``. "Từng byte" là từng byte
của DẠNG CHÍNH TẮC ``v1.chuoi()`` (``sort_keys``, không khoảng trắng), sau khi bỏ
``computed_at`` và ``meta.share_token``; thứ tự khoá của thân thô không được canh.
"""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

import pytest

from tests.golden import v1

# Ghim tệp golden: sinh lại bằng `--ghi` thì phải sửa dòng này, có dấu vết trong diff.
SHA_GOLDEN_HTTP = "7f3581c01b4aedbfe7ed1c4b447a7e7f71c4c17d020dc5a9c813175e0c275c53"

DATA = json.loads(v1.FILE_HTTP.read_text(encoding="utf-8"))
CASES = DATA["cases"]
SIX_ROUTES = {"/v1/la-so-full", "/v1/la-so", "/v1/la-so/luu-nien", "/v1/hop-tuoi",
              "/v1/phong-thuy", "/v1/chon-ngay"}


@pytest.fixture(scope="module")
def client():
    return v1.app_client()


@pytest.fixture
def frozen(monkeypatch):
    v1.dong_bang(monkeypatch.setattr)


def test_golden_file_pinned():
    assert v1.sha_tep(v1.FILE_HTTP) == SHA_GOLDEN_HTTP


def test_golden_contract():
    # Mẫu số: đọc nó, đừng chỉ đọc dòng xanh.
    assert len(CASES) == 104
    assert DATA["ngay_dong_bang"] == v1.NGAY_DONG_BANG
    assert DATA["bo_khi_chuan_hoa"] == ["computed_at", "meta.share_token"]
    assert set(Counter(c["path"] for c in CASES)) == SIX_ROUTES
    assert [{k: c[k] for k in ("id", "method", "path", "params", "json")} for c in CASES] \
        == v1.tao_yeu_cau()
    ok = [c for c in CASES if not c["id"].startswith("err-")]
    loi = [c for c in CASES if c["id"].startswith("err-")]
    assert Counter(c["ket_qua"]["status"] for c in ok) == {200: 88}
    assert Counter(c["ket_qua"]["status"] for c in loi) == {400: 16}
    assert set(Counter(c["path"] for c in loi)) == SIX_ROUTES
    assert all(c["ket_qua"]["body"]["status"] == "error" for c in loi)
    assert Counter(c["ket_qua"]["body"]["error_code"] for c in loi) == {
        "INVALID_INPUT": 15, "RANGE_TOO_LARGE": 1}


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden_v1_http(client, frozen, case):
    actual = v1.goi(client, case)
    assert actual["status"] == case["ket_qua"]["status"]
    assert v1.chuoi(actual["body"]) == v1.chuoi(case["ket_qua"]["body"])


# Mọi lời gọi đọc đồng hồ, theo tên hàm cuối của lời gọi (thuộc tính hay tên trần).
TEN_DONG_HO = {"today", "now", "utcnow", "fromtimestamp", "utcfromtimestamp", "time", "time_ns",
               "monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns", "localtime",
               "gmtime", "ctime", "process_time"}


def _clock_reads() -> Counter:
    src = Path(v1.ROOT / "src")
    found: Counter = Counter()
    for path in src.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            ten = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
            if ten in TEN_DONG_HO:
                found[(str(path.relative_to(src)), ast.unparse(f))] += 1
    return found


def test_clock_reads_are_all_frozen():
    """Một chỗ đọc đồng hồ mới mà `dong_bang` không biết = golden sẽ trôi theo ngày."""
    assert _clock_reads() == Counter({
        # đóng băng trong v1.dong_bang
        ("api/tz.py", "datetime.now"): 1,              # today_in_tz
        ("api/routes/la_so.py", "date.today"): 1,
        ("api/routes/la_so_luu_nien.py", "date.today"): 1,
        ("api/routes/la_so_full.py", "date.today"): 1,
        ("api/routes/tu_tru.py", "date.today"): 1,
        ("api/routes/hop_tuoi.py", "date.today"): 1,
        ("engine/dai_van.py", "dt_date.today"): 1,
        # KHÔNG đóng băng, có lý do
        ("api/version.py", "datetime.now"): 1,         # utc_now_iso → computed_at, bỏ khi chuẩn hoá
        ("api/share.py", "time.time"): 2,              # share_token (ts) và hạn token, bỏ khi chuẩn hoá
        ("api/rate_limit.py", "time.time"): 4,         # khe đếm giới hạn lượt gọi, không vào thân phản hồi
    })
