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
