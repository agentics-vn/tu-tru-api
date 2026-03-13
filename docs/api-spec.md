# API Spec — POST /v1/chon-ngay

## Request
```json
{
  "birth_date":  "1990-05-15",
  "birth_time":  "07:30",
  "intent":      "CUOI_HOI",
  "range_start": "2026-01-01",
  "range_end":   "2026-03-31",
  "top_n":       3
}
```

| Field | Required | Type | Validation |
|---|---|---|---|
| birth_date | Yes | string ISO | Past date, year >= 1900 |
| birth_time | No | HH:MM \| null | 24h format |
| intent | Yes | enum | `KHAI_TRUONG\|KY_HOP_DONG\|CAU_TAI\|NHAM_CHUC\|AN_HOI\|CUOI_HOI\|DAM_CUOI\|CAU_TU\|DONG_THO\|NHAP_TRACH\|LAM_NHA\|MUA_NHA_DAT\|XAY_BEP\|LAM_GIUONG\|DAO_GIENG\|AN_TANG\|CAI_TANG\|XUAT_HANH\|DI_CHUYEN_NGOAI\|TE_TU\|GIAI_HAN\|KHAM_BENH\|PHAU_THUAT\|NHAP_HOC_THI_CU\|KIEN_TUNG\|TRONG_CAY\|MAC_DINH` |
| range_start | Yes | string ISO | Not in past |
| range_end | Yes | string ISO | range_end - range_start <= 90 days |
| top_n | No | integer | 1–10, default 3 |

## Response 200
```json
{
  "status": "success",
  "meta": {
    "intent": "CUOI_HOI",
    "range_scanned": { "from": "2026-01-01", "to": "2026-03-31" },
    "total_days_scanned": 90,
    "days_passed_layer1": 64,
    "days_passed_layer2": 41,
    "bat_tu_summary": {
      "ngu_hanh_menh": "Thủy",
      "duong_than": "Kim",
      "ky_than": "Thổ"
    }
  },
  "recommended_dates": [
    {
      "date": "2026-01-18",
      "lunar_date": "Ngày 29 tháng Chạp năm Ất Tỵ",
      "score": 87,
      "grade": "A",
      "truc": "Thành",
      "sao_cat": ["Thiên Đức", "Nguyệt Đức"],
      "sao_hung": [],
      "nguhanh_day": "Hỏa",
      "reason_vi": "Ngày Thành, có Thiên Đức — rất tốt cho Cưới hỏi. Ngũ hành ngày tương sinh với mệnh chủ nhân.",
      "time_slots": ["07:00-09:00", "11:00-13:00"]
    }
  ],
  "dates_to_avoid": [
    {
      "date": "2026-01-07",
      "reason_vi": "Thiên Khắc Địa Xung với tuổi chủ nhân. Tuyệt đối tránh.",
      "severity": 3
    }
  ]
}
```

## Error Responses
| HTTP | error_code | When |
|---|---|---|
| 400 | INVALID_INPUT | Missing field / validation fail |
| 400 | RANGE_TOO_LARGE | range > 90 days |
| 401 | UNAUTHORIZED | Missing/invalid API key |
| 422 | NO_DATES_FOUND | 0 dates passed all layers |
| 429 | RATE_LIMITED | Over quota |
| 500 | INTERNAL_ERROR | Unexpected server error |

```json
{
  "status": "error",
  "error_code": "INVALID_INPUT",
  "message": "range_end must be within 90 days of range_start"
}
```

## Headers
- `X-API-Key: <key>` — required on all requests
- `X-RateLimit-Remaining: 94` — remaining calls today
- `X-RateLimit-Reset: 1735689600` — Unix timestamp when quota resets

---

# API Spec — GET /v1/lich-thang

Lịch tháng với Hoàng Đạo/Hắc Đạo, giờ tốt, 28 Tú, tóm tắt tốt/xấu.

## Request (Query params)

| Param | Required | Type | Description |
|---|---|---|---|
| birth_date | Yes | string ISO | Ngày sinh YYYY-MM-DD |
| birth_time | No | int | Giờ sinh dropdown |
| gender | No | string | `male` \| `female` |
| month | Yes | string | Tháng cần xem YYYY-MM |

## Response 200
```json
{
  "status": "success",
  "month": "2026-03",
  "user_menh": { "hanh": "Kim", "name": "Hải Trung Kim" },
  "days": [
    {
      "date": "2026-03-01",
      "lunar_day": 13,
      "lunar_month": 1,
      "can_chi_name": "Giáp Thìn",
      "is_hoang_dao": true,
      "star_name": "Kim Quỹ",
      "badge": "hoang_dao",
      "truc_name": "Bình",
      "truc_score": 1,
      "is_layer1_pass": true,
      "gio_hoang_dao": [
        { "chi_name": "Tý", "range": "23:00-01:00" },
        { "chi_name": "Sửu", "range": "01:00-03:00" },
        { "chi_name": "Thìn", "range": "07:00-09:00" },
        { "chi_name": "Tỵ", "range": "09:00-11:00" },
        { "chi_name": "Mùi", "range": "13:00-15:00" },
        { "chi_name": "Tuất", "range": "19:00-21:00" }
      ],
      "sao_28": {
        "name": "Sâm",
        "hanh": "Thủy",
        "tot_xau": "tốt"
      },
      "summary": {
        "tot": ["Hoàng Đạo (Kim Quỹ)", "Sao Sâm"],
        "xau": [],
        "rating": "tốt"
      }
    }
  ]
}
```

---

# API Spec — POST /v1/tu-tru

Lập lá số Tứ Trụ (Four Pillars / Bát Tự) cho một ngày sinh.

## Request
```json
{
  "birth_date": "1990-05-15",
  "birth_time": 8,
  "gender": "male"
}
```

| Field | Required | Type | Validation |
|---|---|---|---|
| birth_date | Yes | string ISO | Past date, year >= 1900 |
| birth_time | No | int | Dropdown: 0,2,4,6,8,10,11,14,16,18,20,22,23 |
| gender | No | string | `male` \| `female` (required for Đại Vận) |

**Notes:**
- `birth_time` omitted → chỉ trả về Mệnh Nạp Âm (year-level info)
- `birth_time` provided → trả đầy đủ Tứ Trụ, Dụng Thần, Thập Thần
- `gender` provided (+ birth_time) → thêm Đại Vận (10-year luck cycles)

## Response 200 — Full (birth_time + gender)
```json
{
  "status": "success",
  "birth_date": "1990-05-15",
  "birth_time": 8,
  "birth_time_label": "Giờ Thìn (7h-8h59)",
  "birth_year_can_chi": "Canh Ngọ",
  "menh": {
    "nap_am_name": "Lộ Bàng Thổ",
    "hanh": "Thổ",
    "duong_than": "Hỏa",
    "ky_than": "Mộc"
  },
  "tu_tru_display": "Canh Ngọ | Tân Tỵ | Đinh Mùi | Giáp Thìn",
  "pillars": {
    "year": {
      "can_chi": "Canh Ngọ",
      "can": { "idx": 6, "name": "Canh" },
      "chi": { "idx": 6, "name": "Ngọ" },
      "nap_am": { "hanh": "Thổ", "name": "Lộ Bàng Thổ" }
    },
    "month": { "..." : "..." },
    "day":   { "..." : "..." },
    "hour":  { "..." : "..." }
  },
  "nhat_chu": {
    "can_name": "Đinh",
    "hanh": "Hỏa"
  },
  "chart_strength": "weak",
  "dung_than": {
    "element": "Mộc",
    "description": "Nguyên tố hỗ trợ tốt nhất cho lá số"
  },
  "hi_than": {
    "element": "Hỏa",
    "description": "Nguyên tố hỗ trợ phụ"
  },
  "ky_than": {
    "element": "Thủy",
    "description": "Nguyên tố bất lợi nhất"
  },
  "cuu_than": {
    "element": "Kim",
    "description": "Nguyên tố sinh ra Kỵ Thần"
  },
  "thap_than": {
    "year": { "key": "chinh_tai", "name": "Chính Tài", "category": "favorable" },
    "month": { "key": "thien_tai", "name": "Thiên Tài", "category": "unfavorable" },
    "hour":  { "key": "chinh_an",  "name": "Chính Ấn",  "category": "favorable" },
    "dominant": { "key": "chinh_tai", "name": "Chính Tài" }
  },
  "gender": "male",
  "dai_van": {
    "direction": "thuận",
    "current": {
      "display": "Nhâm Thân",
      "hanh": "Thủy",
      "nap_am_hanh": "Kim",
      "age_range": "33-42"
    },
    "cycles": [
      {
        "cycle_num": 1,
        "display": "Canh Thìn",
        "hanh": "Kim",
        "nap_am_hanh": "Kim",
        "age_range": "3-12"
      }
    ]
  }
}
```

## Response 200 — Basic (no birth_time)
```json
{
  "status": "success",
  "birth_date": "1990-05-15",
  "birth_year_can_chi": "Canh Ngọ",
  "menh": {
    "nap_am_name": "Lộ Bàng Thổ",
    "hanh": "Thổ",
    "duong_than": "Hỏa",
    "ky_than": "Mộc"
  },
  "_note": "Chỉ có thông tin cơ bản (mệnh Nạp Âm). Cung cấp birth_time để xem đầy đủ Tứ Trụ, Dụng Thần, Thập Thần."
}
```

## Error Responses
| HTTP | error_code | When |
|---|---|---|
| 400 | INVALID_INPUT | Missing/invalid field |
| 401 | UNAUTHORIZED | Missing/invalid API key |
| 429 | RATE_LIMITED | Over quota |
| 500 | INTERNAL_ERROR | Unexpected server error |
