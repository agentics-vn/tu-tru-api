# Tứ Trụ API

REST API trả về ngày tốt (ngày lành) theo lá số Bát Tự, lịch vạn niên truyền thống Việt Nam, và ý định người dùng (khai trương, cưới hỏi, động thổ, v.v.).

---

## Quick Start

```bash
# Cài đặt dependencies (cần Python 3.11+ và uv)
uv sync

# Chạy server dev
uvicorn src.app:app --reload --port 3000

# Chạy tests
uv run pytest

# Chỉ unit tests
uv run pytest tests/unit
```

API sẽ chạy tại `http://localhost:3000`.  
Docs tự động: `http://localhost:3000/docs` (Swagger UI).

---

## Tech Stack

| Layer | Thư viện |
|---|---|
| Framework | FastAPI 0.109+ |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Lịch âm | `lunardate` |
| Cache | Redis (tùy chọn — fallback graceful khi không có) |
| Error tracking | Sentry SDK (tùy chọn) |
| Python | 3.11+ |

---

## Environment Variables

Tạo file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

| Biến | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `PORT` | Không | `3000` | Port server |
| `REDIS_URL` | Không | `redis://localhost:6379` | URL Redis cho cache Layer 1 |
| `CORS_ORIGINS` | Không | `*` | Danh sách origin cho phép, phân cách bằng dấu phẩy (ví dụ `https://app.example.com`) |
| `SHARE_TOKEN_SECRET` | **Có (production)** | *(insecure default)* | Secret ký HMAC cho share token — **phải set trong production** |
| `SENTRY_DSN` | Không | *(trống)* | DSN của Sentry để theo dõi lỗi |
| `SENTRY_ENVIRONMENT` | Không | `production` | Tên môi trường Sentry |
| `SENTRY_TRACES_SAMPLE_RATE` | Không | `0.1` | Tỷ lệ tracing Sentry (0.0–1.0) |

> **Lưu ý:** `CORS_ORIGINS=*` tự động tắt `allow_credentials`. Để dùng cookie/auth header từ browser, phải liệt kê explicit origins (ví dụ `https://app.example.com`).

---

## Endpoints

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Health check |
| **POST** | **`/v1/chon-ngay`** | Chọn ngày tốt theo lá số + ý định |
| POST | `/v1/chon-ngay/detail` | Phân tích chi tiết một ngày cụ thể |
| GET | `/v1/ngay-hom-nay` | Card ngày hôm nay / ngày bất kỳ |
| GET | `/v1/lich-thang` | Lịch tháng với badge tốt/xấu + 28 Tú |
| GET | `/v1/tieu-van` | Tiểu Vận (vận tháng) |
| POST | `/v1/tu-tru` | Tứ Trụ / Bát Tự đầy đủ |
| GET | `/v1/la-so` | Lá số diễn giải (tính cách, sự nghiệp, sức khỏe) |
| POST | `/v1/hop-tuoi` | Hợp tuổi hai người (v1: điểm, v2: phân tích quan hệ) |
| GET | `/v1/phong-thuy` | Gợi ý phong thủy (hướng, màu, số, vật phẩm, Phi Tinh) |
| GET | `/v1/day-detail` | Chi tiết đầy đủ một ngày (cho tính năng so sánh) |
| GET | `/v1/convert-date` | Chuyển đổi dương lịch ↔ âm lịch |
| POST | `/v1/profile` | Lưu hồ sơ ngày sinh |
| GET | `/v1/profile/{id}` | Lấy hồ sơ đã lưu |
| GET | `/v1/share/{token}` | Giải mã share token và replay kết quả |
| GET | `/v1/weekly-summary` | Top 1–3 ngày tốt trong 7 ngày tới |

---

## Cấu trúc dự án

```
tu-tru-api/
├── src/
│   ├── app.py                    # FastAPI app, middleware, routes
│   ├── calendar_service.py       # Facade Layer 1 — get_day_info(), get_user_chart()
│   ├── filter.py                 # Layer 2 — lọc cá nhân + ý định
│   ├── scoring.py                # Layer 3 — tính điểm + grading
│   ├── api/
│   │   ├── errors.py             # Chuẩn hoá error response (bilingual)
│   │   ├── parse_date.py         # Parser dd/mm/yyyy
│   │   ├── share.py              # HMAC share token
│   │   ├── tz.py                 # Timezone helper
│   │   └── routes/               # Một file .py cho mỗi endpoint
│   ├── cache/
│   │   └── redis.py              # Redis Layer 1 cache (graceful fallback)
│   └── engine/                   # Thuật toán thuần tuý (không side effects)
│       ├── bazi_solar.py         # Ranh giới tiết khí / Lập Xuân
│       ├── can_chi.py            # Thiên Can, Địa Chi, Nạp Âm
│       ├── cuong_nhuoc.py        # Phân tích cường/nhược
│       ├── dai_van.py            # Đại Vận (chu kỳ 10 năm)
│       ├── dung_than.py          # Dụng Thần / Hỷ Thần / Kỵ Thần
│       ├── hoang_dao.py          # Hoàng Đạo/Hắc Đạo, giờ tốt/xấu
│       ├── hop_tuoi.py           # Hợp tuổi v2
│       ├── hung_ngay.py          # Hung ngày (Nguyệt Kỵ, Tam Nương, Dương Công Kỵ)
│       ├── la_so.py              # Diễn giải lá số
│       ├── lich_hnd.py           # Solar terms (Ho Ngoc Duc / Meeus)
│       ├── lunar.py              # solar_to_lunar() wrapper
│       ├── nhi_thap_bat_tu.py    # 28 Tú
│       ├── phi_tinh.py           # Cửu Cung Phi Tinh
│       ├── phong_thuy.py         # Phong thuỷ (hướng, màu, vật phẩm)
│       ├── pillars.py            # Tứ Trụ (tính trụ Tháng, Ngày, Giờ)
│       ├── sao_ngay.py           # Sao ngày (60+ hàm check)
│       ├── tang_can.py           # Tàng Can
│       ├── thap_than.py          # Thập Thần
│       └── truc.py               # 12 Trực
├── docs/
│   ├── algorithm.md              # Nguồn sự thật duy nhất cho mọi tính toán
│   ├── api-spec.md               # Chi tiết request/response từng endpoint
│   ├── frontend-design-guide.md  # Hướng dẫn thiết kế UI cho FE team
│   └── seed/                     # Dữ liệu tĩnh (load lúc khởi động)
│       ├── intent-rules.json
│       ├── hung-ngay.json
│       ├── sao-ngay.json
│       ├── truc.json
│       ├── hop-tuoi-readings.json
│       ├── phi-tinh-stars.json
│       ├── phi-tinh-year-center.json
│       ├── phong-thuy-couple-remedies.json
│       └── phong-thuy-purposes.json
└── tests/
    ├── unit/                     # Engine tests, safety invariant
    └── integration/              # End-to-end endpoint tests
```

---

## Pipeline 3 lớp (core logic)

Mỗi ngày trong khoảng được scan qua 3 lớp:

```
Ngày solar
    │
    ▼ Layer 1 — Universal filter
    │  Loại: Nguyệt Kỵ, Tam Nương, Dương Công Kỵ, Trực Phá/Nguy, Tháng Cô Hồn
    │
    ▼ Layer 2 — Personal chart filter  
    │  Severity 3 (cứng): Địa Chi Tương Xung với tuổi, Tháng Cô Hồn + intent blocked
    │  Severity 2 (mềm):  Thiên Can Tương Khắc, Kỵ Thần element
    │
    ▼ Layer 3 — Scoring  
       Base 50 + Trực ±20 + sao cát/hung ± + intent alignment + Tứ Trụ match
       → Score 0–100, Grade A/B/C/D
```

**Invariant an toàn:** Ngày có severity=3 trong `dates_to_avoid` **tuyệt đối không xuất hiện** trong `recommended_dates`. Có guard check cuối trước khi build response và bộ test safety invariant chạy trong CI.

---

## Định dạng ngày

| Endpoint | Định dạng ngày sinh | Ghi chú |
|---|---|---|
| `POST /v1/chon-ngay` | `dd/mm/yyyy` | `15/03/1984` |
| `POST /v1/tu-tru` | `dd/mm/yyyy` | |
| `POST /v1/hop-tuoi` | `dd/mm/yyyy` | |
| `GET /v1/ngay-hom-nay` | `dd/mm/yyyy` | |
| `GET /v1/lich-thang` | `dd/mm/yyyy` | |
| `GET /v1/phong-thuy` | `dd/mm/yyyy` | |
| `GET /v1/la-so` | `dd/mm/yyyy` | |
| Ngày mục tiêu `date=` | `YYYY-MM-DD` | ISO 8601 |
| Tháng `month=` | `YYYY-MM` | |

---

## Intent codes

| Code | Tiếng Việt | Danh mục |
|---|---|---|
| `KHAI_TRUONG` | Khai trương | Kinh doanh |
| `KY_HOP_DONG` | Ký kết hợp đồng | Kinh doanh |
| `CAU_TAI` | Cầu tài lộc | Kinh doanh |
| `NHAM_CHUC` | Nhậm chức | Kinh doanh |
| `AN_HOI` | Lễ ăn hỏi | Hôn nhân |
| `CUOI_HOI` / `DAM_CUOI` | Đám cưới | Hôn nhân |
| `CAU_TU` | Cầu tự | Hôn nhân |
| `DONG_THO` | Động thổ | Xây dựng |
| `NHAP_TRACH` | Nhập trạch | Xây dựng |
| `LAM_NHA` | Làm nhà | Xây dựng |
| `MUA_NHA_DAT` | Mua nhà đất | Xây dựng |
| `XAY_BEP` | Xây bếp | Xây dựng |
| `LAM_GIUONG` | Làm giường | Xây dựng |
| `DAO_GIENG` | Đào giếng | Xây dựng |
| `AN_TANG` | An táng | Tang lễ |
| `CAI_TANG` | Cải táng | Tang lễ |
| `XUAT_HANH` | Xuất hành | Di chuyển |
| `DI_CHUYEN_NGOAI` | Xuất ngoại | Di chuyển |
| `TE_TU` | Tế tự | Tâm linh |
| `GIAI_HAN` | Giải hạn | Tâm linh |
| `KHAM_BENH` | Khám bệnh | Sức khỏe |
| `PHAU_THUAT` | Phẫu thuật | Sức khỏe |
| `NHAP_HOC_THI_CU` | Nhập học / Thi cử | Học tập |
| `KIEN_TUNG` | Kiện tụng | Pháp lý |
| `TRONG_CAY` | Trồng cây | Nông nghiệp |
| `CAT_TOC` | Cắt tóc / Làm tóc | Chăm sóc cá nhân |
| `XAM_MINH` | Xăm mình / Xỏ khuyên | Chăm sóc cá nhân |
| `MAC_DINH` | Sự kiện chung | Chung |

`CUOI_HOI` là alias cho `DAM_CUOI` — cả hai đều được chấp nhận.

---

## Error contract

Mọi lỗi trả về JSON cùng cấu trúc:

```json
{
  "status": "error",
  "error_code": "INVALID_INPUT",
  "message": "Dữ liệu không hợp lệ.",
  "message_en": "Invalid input data."
}
```

| HTTP | `error_code` | Khi nào |
|---|---|---|
| 400 | `INVALID_INPUT` | Field sai / thiếu / ngày không hợp lệ |
| 400 | `RANGE_TOO_LARGE` | Khoảng ngày > 90 ngày |
| 422 | `NO_DATES_FOUND` | Không tìm thấy ngày tốt nào |
| 500 | `INTERNAL_ERROR` | Lỗi server không mong đợi |

---

## Tests

```bash
# Tất cả tests
uv run pytest

# Unit tests (engine + safety invariant)
uv run pytest tests/unit -v

# Integration tests (endpoints end-to-end)
uv run pytest tests/integration -v

# Safety invariant (chạy riêng — chậm hơn, stress test 2025-2027)
uv run pytest tests/unit/test_safety_invariant.py -v
```

CI (GitHub Actions) chạy `uv run pytest tests/unit` khi push vào `main` hoặc mở PR.

---

## Deploy

Dự án đã cấu hình cho **Fly.io** (`fly.toml`) và **Docker** (`Dockerfile`, `docker-compose.yml`).

```bash
# Build image
docker compose up --build

# Deploy Fly.io
fly deploy
```

Tài liệu API chi tiết: [`docs/api-spec.md`](docs/api-spec.md)  
Hướng dẫn thiết kế FE: [`docs/frontend-design-guide.md`](docs/frontend-design-guide.md)  
Thuật toán: [`docs/algorithm.md`](docs/algorithm.md)
