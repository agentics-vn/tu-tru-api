# Frontend Design Guide — Tứ Trụ API

Tài liệu này dành cho **FE team**: giải thích API làm gì, dữ liệu trả về dùng để thiết kế màn hình nào, và các trạng thái UI cần xử lý cho từng endpoint.

---

## Tổng quan — API này làm gì?

API tính **ngày tốt** theo **lá số Bát Tự** (astrology truyền thống Việt Nam). Người dùng cung cấp ngày sinh và mục đích (khai trương, cưới hỏi, động thổ…), API sẽ:

1. **Lọc** ngày xấu khỏi khoảng thời gian được chọn
2. **Tính điểm** từng ngày còn lại theo lá số cá nhân
3. **Trả về** danh sách ngày tốt nhất + danh sách ngày cần tránh

Ngoài ra, API còn cung cấp:
- **Lịch tháng** với badge tốt/xấu cho từng ngày
- **Card ngày hôm nay** với giờ hoàng đạo, giờ hắc đạo
- **Lá số Tứ Trụ** (Four Pillars / Bát Tự) chi tiết
- **Hợp tuổi** hai người
- **Phong thủy** (hướng, màu, số may mắn)
- **Tiểu Vận** (vận tháng)

---

## Khái niệm cần biết

| Thuật ngữ | Nghĩa đơn giản | Hiển thị cho user |
|---|---|---|
| **Mệnh** / **Ngũ Hành Mệnh** | Hành (Kim/Mộc/Thủy/Hỏa/Thổ) của năm sinh | "Mệnh Kim", "Mệnh Thủy"… |
| **Can Chi** | Tên ngày/năm theo lịch can chi | "Giáp Tý", "Ất Sửu"… |
| **Trực** | Đặc tính của ngày theo chu kỳ 12 | "Trực Thành", "Trực Phá"… |
| **Sao Cát** | Sao tốt trong ngày | "Thiên Đức", "Nguyệt Đức"… |
| **Sao Hung** | Sao xấu trong ngày | "Tam Nương", "Nguyệt Kỵ"… |
| **Hoàng Đạo** | Ngày/giờ thuận lợi (badge xanh) | HOÀNG ĐẠO |
| **Hắc Đạo** | Ngày/giờ không thuận (badge đỏ) | HẮC ĐẠO |
| **Dụng Thần** | Hành bổ trợ tốt nhất cho lá số | "Dụng Thần: Thủy" |
| **Kỵ Thần** | Hành bất lợi nhất | "Kỵ Thần: Hỏa" |
| **Tứ Trụ** | 4 cột giờ-ngày-tháng-năm của lá số | Bảng 4 trụ |
| **Đại Vận** | Chu kỳ vận 10 năm | "Đại Vận 33–42 tuổi" |
| **Severity** | Mức độ xấu của ngày cần tránh | 2 = cảnh báo, 3 = tuyệt đối tránh |
| **Grade** | Hạng chữ của ngày tốt | A/B/C/D |

---

## Luồng người dùng chính

```
[Nhập ngày sinh + ý định]
        ↓
[POST /v1/chon-ngay] → recommended_dates + dates_to_avoid
        ↓
[Hiển thị top N ngày tốt dạng card]
        ↓
[Tap vào một ngày] → POST /v1/chon-ngay/detail hoặc GET /v1/day-detail
        ↓
[Hiển thị chi tiết Layer 1 + 2 + 3 + giờ tốt]
```

---

## Chi tiết từng endpoint

---

### 1. `POST /v1/chon-ngay` — Chọn ngày tốt

**Màn hình:** Trang chọn ngày chính.

#### Request

```json
{
  "birth_date": "15/03/1984",
  "birth_time": 8,
  "gender": 1,
  "intent": "KHAI_TRUONG",
  "range_start": "01/05/2026",
  "range_end": "31/05/2026",
  "top_n": 3
}
```

| Field | Bắt buộc | Ghi chú |
|---|---|---|
| `birth_date` | Có | `dd/mm/yyyy`, quá khứ, năm ≥ 1900 |
| `birth_time` | Không | Giờ sinh (dropdown): 0,2,4,6,8,10,11,14,16,18,20,22,23. Có → tính Tứ Trụ đầy đủ |
| `gender` | Không | `1` (nam) hoặc `-1` (nữ). Cần cho Đại Vận |
| `intent` | Có | Xem bảng Intent bên dưới |
| `range_start` / `range_end` | Có | Khoảng tối đa **90 ngày** |
| `top_n` | Không | Mặc định 3, tối đa 10 |
| `profile_id` | Không | ID hồ sơ đã lưu (thay thế birth_date) |

#### Response 200

```json
{
  "status": "success",
  "meta": {
    "intent": "KHAI_TRUONG",
    "range_scanned": { "from": "01/05/2026", "to": "31/05/2026" },
    "total_days_scanned": 31,
    "days_passed_layer1": 22,
    "days_passed_layer2": 17,
    "bat_tu_summary": {
      "ngu_hanh_menh": "Kim",
      "duong_than": "Thổ",
      "ky_than": "Hỏa",
      "summary_vi": "Mệnh bạn thuộc hành Kim...",
      "tu_tru": { ... },
      "dung_than": "Thổ",
      "hi_than": "Kim",
      "chart_strength": "nhược",
      "current_dai_van": {
        "display": "Nhâm Thân",
        "hanh": "Thủy",
        "age_range": "33-42"
      }
    },
    "share_token": "eyJl..."
  },
  "recommended_dates": [
    {
      "date": "2026-05-12",
      "lunar_date": "Ngày 25 tháng Tư năm Bính Ngọ",
      "score": 87,
      "grade": "A",
      "truc": "Thành",
      "sao_cat": ["Thiên Đức", "Nguyệt Đức"],
      "sao_hung": [],
      "nguhanh_day": "Thổ",
      "reason_vi": "Trực Thành — rất tốt cho khai trương...",
      "summary_vi": "Rất tốt — nên chọn ngày này. Điểm tốt: được quý nhân phù trợ...",
      "time_slots": [
        { "chi_name": "Thìn", "range": "07:00-09:00" },
        { "chi_name": "Tỵ",   "range": "09:00-11:00" }
      ],
      "render_card": {
        "headline": "Ngày 2026-05-12",
        "lunar_line": "Ngày 25 tháng Tư năm Bính Ngọ",
        "badge": "A",
        "score_pct": 87,
        "intent_vi": "KHAI_TRUONG",
        "element": "Thổ",
        "truc": "Thành",
        "stars": ["Thiên Đức", "Nguyệt Đức"],
        "one_liner": "Rất tốt — nên chọn ngày này.",
        "best_hours": ["07:00-09:00", "09:00-11:00", "13:00-15:00"]
      }
    }
  ],
  "dates_to_avoid": [
    {
      "date": "2026-05-05",
      "reason_vi": "Địa Chi ngày Hợi xung với tuổi Tỵ. Tuyệt đối tránh.",
      "severity": 3,
      "summary_vi": "Ngày này xung khắc trực tiếp với tuổi của bạn..."
    },
    {
      "date": "2026-05-07",
      "reason_vi": "Thiên Can ngày khắc Thiên Can tuổi.",
      "severity": 2
    }
  ]
}
```

#### Các trường quan trọng cho FE

**`recommended_dates[n]`**

| Field | Dùng để hiển thị |
|---|---|
| `date` | YYYY-MM-DD — dùng làm key và format ngày |
| `lunar_date` | Hiển thị tên ngày âm lịch dưới ngày dương |
| `score` | Số 0–100 — có thể hiển thị dạng progress bar |
| `grade` | `A/B/C/D` — badge màu (A=xanh, B=lam, C=vàng, D=đỏ) |
| `truc` | Tên trực (Thành, Khai, Mãn…) |
| `sao_cat` | Danh sách sao tốt, hiển thị tag |
| `sao_hung` | Danh sách sao xấu (cảnh báo nhỏ) |
| `summary_vi` | Đoạn văn giải thích ngắn — hiển thị trực tiếp cho user |
| `time_slots` | 6 giờ hoàng đạo — hiển thị chip giờ |
| `render_card` | **Sẵn sàng render** — dùng toàn bộ object này cho card UI |

**`dates_to_avoid[n]`**

| `severity` | Ý nghĩa | UI đề xuất |
|---|---|---|
| `3` | Xung trực tiếp — tuyệt đối tránh | Icon ⛔, màu đỏ, tooltip từ `summary_vi` |
| `2` | Cảnh báo — nên tránh nếu có thể | Icon ⚠️, màu vàng |

**`meta.bat_tu_summary`**

Hiển thị cho user biết lá số của họ. `summary_vi` là đoạn văn plain-language phù hợp để đặt trong accordion/modal "Lá số của bạn".

#### Trạng thái UI cần xử lý

| Trạng thái | Điều kiện | UI |
|---|---|---|
| Loading | Request đang chạy | Skeleton cards |
| Không có ngày tốt | HTTP 422, `error_code: NO_DATES_FOUND` | Thông báo gợi ý mở rộng khoảng ngày |
| Khoảng ngày quá dài | HTTP 400, `error_code: RANGE_TOO_LARGE` | Inline error trên date picker |
| Ngày sinh tương lai | HTTP 400, `error_code: INVALID_INPUT` | Inline error trên field ngày sinh |
| Kết quả rỗng sau lọc | `recommended_dates: []` (không xảy ra — server trả 422) | — |

---

### 2. `POST /v1/chon-ngay/detail` — Phân tích một ngày

**Màn hình:** Drawer/modal sau khi người dùng tap vào một ngày cụ thể để xem chi tiết.

#### Request

```json
{
  "birth_date": "15/03/1984",
  "birth_time": 8,
  "gender": 1,
  "intent": "KHAI_TRUONG",
  "date": "12/05/2026"
}
```

#### Response 200

```json
{
  "status": "success",
  "date": "2026-05-12",
  "lunar_date": "Ngày 25 tháng Tư năm Bính Ngọ",
  "can_chi_day": "Nhâm Tuất",
  "nguhanh_day": "Thổ",
  "verdict": "Rất tốt",
  "verdict_vi": "Ngày rất tốt — nên chọn.",
  "severity": 0,
  "score": 87,
  "grade": "A",
  "layer1": {
    "is_pass": true,
    "truc": { "name": "Thành", "idx": 8, "score": 2 },
    "hung_ngay": {
      "is_nguyet_ky": false,
      "is_tam_nuong": false,
      "is_duong_cong_ky": false
    },
    "is_truc_pha": false,
    "is_truc_nguy": false,
    "sao_tot": {
      "thien_duc": true,
      "thien_duc_hop": false,
      "nguyet_duc": true,
      "nguyet_duc_hop": false,
      "thien_xa": false
    }
  },
  "layer2": {
    "is_pass": true,
    "severity": 0,
    "reasons": [],
    "ngu_hanh_match": {
      "day_hanh": "Thổ",
      "menh_hanh": "Kim",
      "relation": "ngày sinh mệnh (tốt)"
    },
    "dia_chi_clash": false
  },
  "layer3": {
    "base_score": 50,
    "final_score": 87,
    "grade": "A",
    "breakdown": [
      { "source": "Trực Thành", "points": 20, "reason_vi": "Trực Thành — ngày tốt", "type": "bonus" },
      { "source": "Thiên Đức",  "points": 15, "reason_vi": "Ngày có Thiên Đức", "type": "bonus" }
    ],
    "bonus_sao": ["Thiên Đức", "Nguyệt Đức"],
    "penalty_sao": []
  },
  "time_slots": [
    { "chi_name": "Thìn", "range": "07:00-09:00" },
    { "chi_name": "Tỵ",   "range": "09:00-11:00" }
  ],
  "reason_vi": "Trực Thành — rất tốt...",
  "summary_vi": "Rất tốt — nên chọn ngày này."
}
```

#### Thiết kế UI

- **`verdict`** → headline lớn (Rất tốt / Tốt / Chấp nhận được / Cấm)
- **`layer3.breakdown`** → danh sách điểm cộng/trừ, có thể hiển thị dạng timeline
- **`time_slots`** → 6 chip giờ hoàng đạo
- **`layer1.hung_ngay`** + **`layer1.sao_tot`** → section "Sao ngày"
- **`layer2.ngu_hanh_match.relation`** → badge tương sinh/tương khắc

Khi ngày **không qua Layer 1** (`layer1.is_pass: false`): `layer2` và `layer3` là `null`. Chỉ hiển thị lý do Layer 1 từ `layer1_fail_reasons[]`.

Khi ngày **không qua Layer 2** (`layer2.is_pass: false`): `layer3` là `null`. `verdict` = "Cấm", `severity` = 3.

---

### 3. `GET /v1/ngay-hom-nay` — Card ngày hôm nay

**Màn hình:** Dashboard / Home screen — card đầu trang.

#### Request (query params)

```
birth_date=15/03/1984
date=2026-05-12          (tuỳ chọn, mặc định = hôm nay)
birth_time=8             (tuỳ chọn)
gender=1                 (tuỳ chọn)
tz=Asia/Ho_Chi_Minh      (tuỳ chọn)
```

#### Response 200

```json
{
  "status": "success",
  "date": "2026-05-12",
  "can_chi": {
    "name": "Nhâm Tuất",
    "can_name": "Nhâm",
    "chi_name": "Tuất",
    "nap_am_hanh": "Thổ"
  },
  "lunar": {
    "day": 25,
    "month": 4,
    "year": 2026,
    "display": "Ngày 25 tháng Tư năm Bính Ngọ"
  },
  "hoang_dao": {
    "is_hoang_dao": true,
    "star_name": "Kim Quỹ",
    "badge": "HOÀNG ĐẠO"
  },
  "truc": {
    "name": "Thành",
    "score": 2
  },
  "good_for": ["Khai trương", "Ký kết hợp đồng", "Nhập trạch"],
  "avoid_for": ["Phẫu thuật"],
  "gio_tot": [
    { "chi_name": "Thìn", "range": "07:00-09:00" },
    { "chi_name": "Tỵ",   "range": "09:00-11:00" },
    { "chi_name": "Ngọ",  "range": "11:00-13:00" },
    { "chi_name": "Thân", "range": "15:00-17:00" },
    { "chi_name": "Hợi",  "range": "21:00-23:00" },
    { "chi_name": "Tý",   "range": "23:00-01:00" }
  ],
  "gio_xau": [
    { "chi_name": "Dần", "range": "03:00-05:00" }
  ],
  "daily_advice": {
    "nen_lam": "Hoàng Đạo (Kim Quỹ) — thuận lợi. Phù hợp: Khai trương, Ký kết.",
    "nen_tranh": "Không có gì đặc biệt."
  },
  "bat_tu": {
    "tu_tru_display": "...",
    "nhat_chu": { "can_name": "Giáp", "hanh": "Mộc" },
    "dung_than": "Thủy",
    "chart_strength": "nhược",
    "day_thap_than": "Chính Tài",
    "dai_van": {
      "display": "Nhâm Thân",
      "hanh": "Thủy",
      "age_range": "33-42"
    }
  }
}
```

> `bat_tu` chỉ có khi request gửi `birth_time`.

#### Thiết kế UI

```
┌─────────────────────────────────────────┐
│  Thứ Ba, 12/05/2026                      │
│  Ngày 25 tháng Tư năm Bính Ngọ          │
│                                         │
│  Nhâm Tuất  ·  Hành Thổ                 │
│  Trực Thành  ·  [HOÀNG ĐẠO]            │
├─────────────────────────────────────────┤
│  Giờ tốt: 07:00 09:00 11:00 15:00...   │
├─────────────────────────────────────────┤
│  Nên làm: Khai trương, Ký kết hợp đồng │
│  Nên tránh: Phẫu thuật                 │
└─────────────────────────────────────────┘
```

- `hoang_dao.badge` → pill badge màu xanh (`HOÀNG ĐẠO`) hoặc đỏ/xám (`HẮC ĐẠO`)
- `gio_tot` → luôn có đúng 6 giờ — hiển thị dạng chip cuộn ngang
- `good_for` / `avoid_for` → 2 list, giới hạn 5 item mỗi list
- `bat_tu` (khi có) → có thể expandable section "Cá nhân hoá theo lá số"

---

### 4. `GET /v1/lich-thang` — Lịch tháng

**Màn hình:** Calendar view, hiển thị tháng đầy đủ.

#### Request

```
birth_date=15/03/1984
month=2026-05
birth_time=8   (tuỳ chọn)
```

#### Response 200

```json
{
  "status": "success",
  "month": "2026-05",
  "user_menh": { "hanh": "Kim", "name": "Hải Trung Kim" },
  "days": [
    {
      "date": "2026-05-01",
      "lunar_day": 14,
      "lunar_month": 4,
      "can_chi_name": "Nhâm Tuất",
      "is_hoang_dao": false,
      "star_name": "Bạch Hổ",
      "badge": "hac_dao",
      "truc_name": "Bình",
      "truc_score": 1,
      "is_layer1_pass": false,
      "gio_hoang_dao": [
        { "chi_name": "Tý", "range": "23:00-01:00" }
      ],
      "sao_28": {
        "name": "Giác",
        "hanh": "Mộc",
        "tot_xau": "tốt"
      },
      "summary": {
        "tot": ["Sao Giác"],
        "xau": ["Hắc Đạo (Bạch Hổ)", "Nguyệt Kỵ"],
        "rating": "xấu"
      }
    }
  ]
}
```

#### Thiết kế UI — Calendar cell

Mỗi ô ngày trong lịch cần thể hiện:

```
┌──────────────────┐
│ 12               │  ← date (solar)
│ 25               │  ← lunar_day
│ [HOÀNG ĐẠO]      │  ← badge: "hoang_dao" | "hac_dao"
│ Trực Thành        │  ← truc_name
│ ● Thiên Đức       │  ← summary.tot (tối đa 2)
└──────────────────┘
```

**Màu sắc ô:**

| Điều kiện | Màu ô |
|---|---|
| `is_layer1_pass: false` | Xám nhạt / strikethrough |
| `summary.rating: "tốt"` + `is_hoang_dao: true` | Xanh lá nhạt |
| `summary.rating: "tốt"` | Xanh lam nhạt |
| `summary.rating: "bình thường"` | Trắng |
| `summary.rating: "xấu"` | Đỏ rất nhạt |
| `is_hoang_dao: true` | Thêm dot vàng hoặc border |

**Chi tiết khi tap ô:** gọi `GET /v1/day-detail` với ngày đó.

---

### 5. `GET /v1/day-detail` — Chi tiết ngày từ lịch tháng

**Màn hình:** Bottom sheet / Drawer khi tap vào ô lịch tháng.

#### Request

```
birth_date=15/03/1984
date=2026-05-12
birth_time=8      (tuỳ chọn)
gender=1          (tuỳ chọn)
intent=KHAI_TRUONG (tuỳ chọn, mặc định MAC_DINH)
```

Response có cùng cấu trúc với `POST /v1/chon-ngay/detail` — xem phần 2.

---

### 6. `POST /v1/tu-tru` — Lá số Tứ Trụ

**Màn hình:** Màn hình "Lá số của tôi" / Xem chi tiết Bát Tự.

#### Request

```json
{
  "birth_date": "15/03/1984",
  "birth_time": 8,
  "gender": 1
}
```

Khi **không có `birth_time`**: API chỉ trả mệnh cơ bản.  
Khi **có `birth_time`**: API trả đầy đủ Tứ Trụ + Dụng Thần + Thập Thần.  
Khi **có cả `birth_time` + `gender`**: Thêm Đại Vận.

#### Response 200 — Đầy đủ

```json
{
  "status": "success",
  "birth_date": "1984-03-15",
  "birth_year_can_chi": "Giáp Tý",
  "menh": {
    "nap_am_name": "Hải Trung Kim",
    "hanh": "Kim",
    "duong_than": "Thổ",
    "ky_than": "Hỏa"
  },
  "birth_time": 8,
  "birth_time_label": "Giờ Thìn (7h-8h59)",
  "tu_tru_display": "Giáp Tý | Ất Mão | Canh Tuất | Giáp Thìn",
  "pillars": {
    "year":  { "can_chi": "Giáp Tý",  "can": {"idx":0,"name":"Giáp"}, "chi": {"idx":0,"name":"Tý"},   "nap_am": {"hanh":"Kim","name":"Hải Trung Kim"} },
    "month": { "can_chi": "Ất Mão",   "can": {"idx":1,"name":"Ất"},   "chi": {"idx":3,"name":"Mão"},   "nap_am": {"hanh":"Thủy","name":"Đại Khê Thủy"} },
    "day":   { "can_chi": "Canh Tuất","can": {"idx":6,"name":"Canh"}, "chi": {"idx":10,"name":"Tuất"}, "nap_am": {"hanh":"Kim","name":"Thoa Xuyến Kim"} },
    "hour":  { "can_chi": "Giáp Thìn","can": {"idx":0,"name":"Giáp"}, "chi": {"idx":4,"name":"Thìn"},  "nap_am": {"hanh":"Hỏa","name":"Phú Đăng Hỏa"} }
  },
  "nhat_chu": { "can_name": "Canh", "hanh": "Kim" },
  "chart_strength": "nhược",
  "element_counts": { "Kim": 2.5, "Mộc": 1.0, "Thủy": 1.5, "Hỏa": 0.5, "Thổ": 2.0 },
  "support_ratio": 0.33,
  "dung_than": { "element": "Thổ", "description": "Nguyên tố hỗ trợ tốt nhất cho lá số" },
  "hi_than":   { "element": "Hỏa", "description": "Nguyên tố hỗ trợ phụ" },
  "ky_than":   { "element": "Mộc", "description": "Nguyên tố bất lợi nhất" },
  "cuu_than":  { "element": "Thủy","description": "Nguyên tố sinh ra Kỵ Thần" },
  "thap_than": {
    "year":  { "key": "chinh_an",  "name": "Chính Ấn",  "category": "favorable" },
    "month": { "key": "kiep_tai",  "name": "Kiếp Tài",  "category": "unfavorable" },
    "hour":  { "key": "thinh_tai", "name": "Thực Thần", "category": "favorable" },
    "dominant": { "key": "chinh_an", "name": "Chính Ấn" }
  },
  "gender": 1,
  "dai_van": {
    "direction": "thuận",
    "current": {
      "display": "Nhâm Thân",
      "hanh": "Thủy",
      "nap_am_hanh": "Kim",
      "age_range": "33-42"
    },
    "cycles": [
      { "cycle_num": 1, "display": "Bính Ngọ", "hanh": "Hỏa", "nap_am_hanh": "Thiên Hà Thủy", "age_range": "3-12" },
      { "cycle_num": 2, "display": "Đinh Mùi",  "hanh": "Hỏa", "nap_am_hanh": "Thiên Hà Thủy", "age_range": "13-22" }
    ]
  }
}
```

#### Thiết kế UI

**Bảng Tứ Trụ (4 trụ):**

```
┌──────────┬──────────┬──────────┬──────────┐
│   NĂM    │  THÁNG   │   NGÀY   │   GIỜ    │
│  Giáp Tý │  Ất Mão  │Canh Tuất │Giáp Thìn │
│   (Kim)  │  (Thủy)  │   (Kim)  │  (Hỏa)   │
└──────────┴──────────┴──────────┴──────────┘
              Nhật Chủ: Canh Kim
```

**Biểu đồ ngũ hành (`element_counts`):**

Dùng để vẽ biểu đồ tỷ lệ. Tính phần trăm từ `element_counts`:
```
total = sum(element_counts.values())
pct_Kim = element_counts.Kim / total * 100
```

**Cường/nhược (`chart_strength`):**
- `"vượng"` → thân vượng, nên hành khai thông
- `"nhược"` → thân nhược, cần bổ trợ
- `"cân bằng"` → cân bằng

**Đại Vận:**

Timeline ngang, mỗi đoạn là 10 năm. Highlight đoạn `current`.

```
3–12    13–22   23–32   [33–42]   43–52
Bính Ngọ Đinh Mùi ...   Nhâm Thân  ...
  Hỏa     Hỏa           Thủy (hiện tại)
```

---

### 7. `GET /v1/la-so` — Lá số diễn giải

**Màn hình:** "Khám phá lá số" — trang profile sâu hơn, dùng để LLM hoặc template sinh văn xuôi.

**Khác `POST /v1/tu-tru`:** `birth_time` bắt buộc, trả thêm archetype tính cách, sự nghiệp, sức khỏe, tình duyên.

#### Request

```
birth_date=15/03/1984&birth_time=8&gender=1
```

#### Cấu trúc response chính

| Trường | Dùng để |
|---|---|
| `tinh_cach.archetype` | Tên nhân vật (ví dụ "Ngọn nến") — headline card |
| `tinh_cach.core_traits[]` | Danh sách tính cách chính — chip list |
| `tinh_cach.strength_note` | Giải thích cường/nhược bằng lời — paragraph |
| `su_nghiep.career_tendency` | Xu hướng nghề nghiệp — paragraph |
| `su_nghiep.suitable_fields[]` | Ngành phù hợp — chip list |
| `tai_van.wealth_style` | Phong cách tài vận — paragraph |
| `suc_khoe.organ` | Cơ quan dễ ảnh hưởng — label |
| `suc_khoe.health_context` | `risk_when_weak` hoặc `risk_when_strong` — chọn text hiển thị |
| `tinh_duyen` | Tín hiệu tình duyên (chỉ khi có `gender`) |
| `dai_van_current` | Đại Vận hiện tại (chỉ khi có `gender`) |
| `_raw.element_counts` | Dùng vẽ biểu đồ ngũ hành |

---

### 8. `POST /v1/hop-tuoi` — Hợp tuổi

**Màn hình:** "Kiểm tra hợp tuổi" — nhập ngày sinh 2 người.

Có 2 mode:
- **v1** (không gửi `relationship_type`): trả điểm số + grade tổng hợp
- **v2** (gửi `relationship_type`): phân tích định tính theo loại quan hệ

#### Request v2

```json
{
  "person1_birth_date": "15/03/1984",
  "person1_birth_time": 8,
  "person1_gender": 1,
  "person2_birth_date": "20/08/1990",
  "person2_birth_time": 10,
  "person2_gender": -1,
  "relationship_type": "PHU_THE"
}
```

#### Response v1

```json
{
  "status": "success",
  "version": 1,
  "person1": { "birth_date": "1984-03-15", "menh": "Hải Trung Kim", "hanh": "Kim", "nhatChu": "Canh Kim", "gender": 1 },
  "person2": { "birth_date": "1990-08-20", "menh": "Lộ Bàng Thổ",  "hanh": "Thổ", "nhatChu": "Đinh Hỏa", "gender": -1 },
  "overall_score": 78,
  "grade": "B",
  "ngu_hanh_relation": "Tương Sinh",
  "details": [
    { "category": "Ngũ Hành Nạp Âm", "score": 90, "description": "Kim và Thổ — Tương Sinh." },
    { "category": "Nhật Chủ tương tác", "score": 75, "description": "..." },
    { "category": "Địa Chi", "score": 80, "description": "Địa Chi không xung — ổn định." },
    { "category": "Thiên Can", "score": 70, "description": "..." }
  ],
  "summary": "Hai lá số rất tương hợp...",
  "advice": "Nên chọn ngày có hành Kim hoặc Thổ..."
}
```

#### Response v2

```json
{
  "status": "success",
  "version": 2,
  "relationship_type": "PHU_THE",
  "relationship_label": "Phu Thê",
  "person1": { ... },
  "person2": { ... },
  "verdict": "Tương hợp",
  "verdict_level": 2,
  "criteria": [
    { "name": "Ngũ Hành Nạp Âm", "sentiment": "positive", "description": "Kim và Thổ tương sinh — nền tảng vững." },
    { "name": "Lục Hợp", "sentiment": "neutral", "description": "Không có Lục Hợp — không thêm điểm." }
  ],
  "reading": "Hai người có nền tảng ngũ hành thuận lợi...",
  "advice": "Nên chọn ngày lễ cưới vào tháng có hành Thổ hoặc Kim..."
}
```

#### Thiết kế UI

**v1 — Score card:**
```
┌────────────────────────────────────┐
│ Tương Sinh  ·  Grade B  ·  78/100  │
│ ████████░░ 78%                     │
├────────────────────────────────────┤
│ Ngũ Hành Nạp Âm    90 ██████████  │
│ Nhật Chủ           75 ████████     │
│ Địa Chi            80 █████████    │
│ Thiên Can          70 ███████      │
└────────────────────────────────────┘
```

**v2 — Verdict + Criteria:**
- `verdict_level` 1–4 → màu badge (1=xanh, 2=lam, 3=vàng, 4=đỏ)
- `criteria[n].sentiment` → icon: `positive`=✅, `neutral`=〰️, `negative`=⚠️

**Dropdown `relationship_type`:**

| Giá trị | Hiển thị | Đối xứng |
|---|---|---|
| `PHU_THE` | 💑 Phu Thê | Có |
| `DOI_TAC` | 🤝 Đối Tác | Có |
| `SEP_NHAN_VIEN` | 👔 Sếp — Nhân Viên | Người 1 là sếp |
| `DONG_NGHIEP` | 🏢 Đồng Nghiệp | Có |
| `BAN_BE` | 👫 Bạn Bè | Có |
| `PHU_TU` | 👨‍👦 Cha Mẹ — Con | Người 1 là cha/mẹ |
| `ANH_CHI_EM` | 👨‍👧‍👦 Anh Chị Em | Có |
| `THAY_TRO` | 📚 Thầy — Trò | Người 1 là thầy |

---

### 9. `GET /v1/phong-thuy` — Phong thủy

**Màn hình:** Tab "Phong thủy" — hướng tốt, màu, số may mắn, gợi ý vật phẩm.

#### Request

```
birth_date=15/03/1984
purpose=NHA_O           (NHA_O | VAN_PHONG | CUA_HANG | PHONG_KHACH)
year=2026               (tuỳ chọn — thêm Phi Tinh)
partner_birth_date=20/08/1990  (tuỳ chọn — hóa giải cặp)
birth_time=8            (tuỳ chọn — cá nhân hóa)
```

#### Cấu trúc response

```json
{
  "status": "success",
  "version": 2,
  "purpose": "NHA_O",
  "user_menh": { "hanh": "Kim", "name": "Hải Trung Kim" },
  "dung_than": "Thổ",
  "ky_than": "Hỏa",
  "huong_tot": ["Đông Bắc", "Tây Nam"],
  "huong_xau": [{ "huong": "Nam", "ly_do": "Hướng Hỏa, tương khắc Kim" }],
  "mau_may_man": ["Vàng đất", "Nâu", "Trắng"],
  "mau_ky": ["Đỏ", "Cam"],
  "so_may_man": [2, 5, 8],
  "so_ky": [7, 9],
  "vat_pham": [
    { "item": "Tượng trâu đồng", "element": "Thổ", "placement": "Phía Đông Bắc", "reason": "Bổ trợ Dụng Thần Thổ" }
  ],
  "purpose_specific": {
    "huong_cua": { "tot": "Đông Bắc", "ly_do": "Dụng Thần Thổ, thu hút tài lộc" }
  },
  "personalization": {
    "chart_strength": "nhược",
    "intensity": "vừa",
    "note": "Lá số thân nhược — ưu tiên vật phẩm bổ trợ Thổ mạnh hơn.",
    "extra_items": []
  },
  "phi_tinh_year": 2026,
  "phi_tinh": [
    { "direction": "Đông Nam", "star": 4, "star_name": "Tứ Lục Văn Xương", "hanh": "Mộc", "nature": "tốt", "meaning": "Văn học, học hành" }
  ],
  "huong_tot_nam_nay": ["Đông Nam", "Bắc"],
  "huong_xau_nam_nay": ["Tây", "Tây Nam"],
  "hoa_giai": [
    { "direction": "Tây", "star": 3, "remedy": "Đặt vật phẩm Kim loại để hóa giải sao Tam Bích" }
  ],
  "couple_harmony": {
    "relation": "Tương Khắc (Mộc khắc Thổ)",
    "remedy_element": "Hỏa",
    "remedies": ["Đèn đỏ", "Nến đỏ"],
    "colors_for_shared_space": ["Đỏ nhạt", "Tím"]
  }
}
```

#### Thiết kế UI

**Tabs theo `purpose`:**

```
[Nhà ở]  [Văn phòng]  [Cửa hàng]  [Phòng khách]
```

**La bàn hướng tốt/xấu:**

Vẽ compass 8 hướng. Tô xanh = `huong_tot`, tô đỏ = `huong_xau`.  
Khi có `year`: overlay thêm `huong_tot_nam_nay` / `huong_xau_nam_nay`.

**Màu sắc:**

```
May mắn: ■ Vàng đất  ■ Nâu  ■ Trắng
Nên tránh: ■ Đỏ  ■ Cam
```

**Phi Tinh grid (khi có `year`):**

Hiển thị lưới 3×3 Cửu Cung. Mỗi ô có tên sao + `nature`:
- `tốt` → nền xanh nhạt
- `xấu` → nền đỏ nhạt
- `trung` → nền xám nhạt

**`couple_harmony`:** Chỉ xuất hiện khi 2 người **tương khắc**. Nếu field này không có trong response, **không hiển thị section hóa giải**.

---

### 10. `GET /v1/tieu-van` — Tiểu Vận (vận tháng)

**Màn hình:** Section nhỏ trên calendar hoặc tab vận tháng.

#### Request

```
birth_date=15/03/1984
month=2026-05
```

#### Response

```json
{
  "status": "success",
  "month": "2026-05",
  "user_menh": { "hanh": "Kim", "name": "Hải Trung Kim" },
  "tieu_van_pillar": {
    "can_name": "Nhâm",
    "chi_name": "Thân",
    "display": "Nhâm Thân",
    "nap_am_hanh": "Kim"
  },
  "element_relation": "tuong_sinh",
  "reading": "Tháng Nhâm Thân — Kim sinh Kim, năng lượng bổ trợ tốt cho mệnh Kim...",
  "tags": ["Thuận lợi", "Tài vận tốt"]
}
```

| `element_relation` | Ý nghĩa | Hiển thị |
|---|---|---|
| `tuong_sinh` | Tháng sinh mệnh — rất tốt | Badge xanh |
| `bi_sinh` | Mệnh sinh tháng — hao tốn chút | Badge vàng nhạt |
| `tuong_khac` | Tháng khắc mệnh — cần cẩn thận | Badge đỏ |
| `bi_khac` | Mệnh khắc tháng — ổn | Badge xanh nhạt |
| `binh_hoa` | Cùng hành — bình ổn | Badge xám |

---

### 11. `GET /v1/convert-date` — Chuyển đổi lịch

**Màn hình:** Tiện ích nhỏ — người dùng tra cứu ngày âm/dương.

```
Dương → Âm:   solar=2026-05-12
Âm → Dương:   lunar_year=2026&lunar_month=4&lunar_day=25
```

Response đơn giản:

```json
{
  "status": "success",
  "direction": "solar_to_lunar",
  "result": {
    "lunar_year": 2026,
    "lunar_month": 4,
    "lunar_day": 25,
    "is_leap_month": false,
    "display_vi": "Ngày 25 tháng Tư"
  }
}
```

---

### 12. `GET /v1/weekly-summary` — Tóm tắt tuần

**Màn hình:** Widget push notification / dashboard "Ngày tốt tuần này".

```
birth_date=15/03/1984
intent=KHAI_TRUONG
```

```json
{
  "status": "success",
  "week_start": "2026-05-10",
  "week_end": "2026-05-16",
  "intent": "KHAI_TRUONG",
  "top_dates": [
    {
      "date": "2026-05-12",
      "score": 87,
      "grade": "A",
      "one_liner": "Rất tốt — nên chọn ngày này.",
      "best_hours": [
        { "chi_name": "Thìn", "range": "07:00-09:00" }
      ]
    }
  ],
  "count": 1
}
```

Khi `count: 0` → "Tuần này không có ngày tốt cho mục đích bạn chọn."

---

### 13. `POST /v1/profile` + `GET /v1/profile/{id}` — Lưu hồ sơ

Cho phép user lưu ngày sinh một lần và dùng `profile_id` thay thế cho mọi request sau.

```
POST /v1/profile?birth_date=15/03/1984&birth_time=8&gender=1
→ { "profile_id": "a3f9c12b8e1d" }
```

Sau đó dùng trong các request:

```json
{
  "profile_id": "a3f9c12b8e1d",
  "intent": "KHAI_TRUONG",
  "range_start": "01/05/2026",
  "range_end": "31/05/2026"
}
```

---

### 14. `GET /v1/share/{token}` — Chia sẻ kết quả

Khi gọi `POST /v1/chon-ngay`, response có `meta.share_token`. Dùng để tạo URL chia sẻ:

```
https://app.example.com/ket-qua?token=eyJl...
```

Khi load trang chia sẻ, FE gọi:

```
GET /v1/share/{token}
```

API sẽ replay query và trả kết quả. Token có hiệu lực 90 ngày.

---

## Xử lý lỗi chung

Mọi error response đều có cùng cấu trúc:

```json
{
  "status": "error",
  "error_code": "INVALID_INPUT",
  "message": "Ngày sinh phải là ngày trong quá khứ",
  "message_en": "Birth date must be in the past"
}
```

| `error_code` | Nguyên nhân phổ biến | UI |
|---|---|---|
| `INVALID_INPUT` | Field sai định dạng, ngày tương lai, giờ sinh không hợp lệ | Inline validation error |
| `RANGE_TOO_LARGE` | Khoảng ngày > 90 ngày | "Vui lòng chọn khoảng tối đa 90 ngày" |
| `NO_DATES_FOUND` | Không có ngày tốt nào | "Không tìm được ngày phù hợp. Thử mở rộng khoảng thời gian." |
| `INTERNAL_ERROR` | Lỗi server | Toast "Đã có lỗi xảy ra. Vui lòng thử lại." + retry |

---

## Giờ sinh — dropdown hợp lệ

Chỉ được gửi các giá trị: **0, 2, 4, 6, 8, 10, 11, 14, 16, 18, 20, 22, 23**

| Giá trị | Nhãn hiển thị |
|---|---|
| 23 | Giờ Tý Muộn (23h-23h59) |
| 0 | Giờ Tý Sớm (0h-0h59) |
| 2 | Giờ Sửu (1h-2h59) |
| 4 | Giờ Dần (3h-4h59) |
| 6 | Giờ Mão (5h-6h59) |
| 8 | Giờ Thìn (7h-8h59) |
| 10 | Giờ Tỵ (9h-10h59) |
| 11 | Giờ Ngọ (11h-12h59) |
| 14 | Giờ Mùi (13h-14h59) |
| 16 | Giờ Thân (15h-16h59) |
| 18 | Giờ Dậu (17h-18h59) |
| 20 | Giờ Tuất (19h-20h59) |
| 22 | Giờ Hợi (21h-22h59) |

---

## Ngũ Hành — màu gợi ý

| Hành | Màu gợi ý | Hex |
|---|---|---|
| **Kim** | Trắng, Bạc | `#F5F5F5`, `#C0C0C0` |
| **Mộc** | Xanh lá | `#4CAF50`, `#81C784` |
| **Thủy** | Xanh dương | `#2196F3`, `#64B5F6` |
| **Hỏa** | Đỏ, Cam | `#F44336`, `#FF7043` |
| **Thổ** | Vàng đất, Nâu | `#FF9800`, `#8D6E63` |

---

## Grade — màu badge

| Grade | Màu | Ý nghĩa |
|---|---|---|
| **A** | `#4CAF50` Xanh lá | Rất tốt — nên chọn |
| **B** | `#2196F3` Xanh lam | Tốt — có thể chọn |
| **C** | `#FF9800` Cam | Chấp nhận được |
| **D** | `#9E9E9E` Xám | Không tốt — nên tránh |

---

## Tài liệu liên quan

- [README.md](../README.md) — Tổng quan dự án, cài đặt, deploy
- [api-spec.md](api-spec.md) — Chi tiết kỹ thuật từng endpoint (dành cho BE/integration)
- [algorithm.md](algorithm.md) — Thuật toán tính toán (nguồn sự thật)
