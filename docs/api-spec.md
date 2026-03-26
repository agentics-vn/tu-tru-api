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

---

# API Spec — POST /v1/hop-tuoi

So khớp tuổi / hợp tuổi giữa hai người. Một endpoint, hai chế độ trả lời:

- **v1** (mặc định): bỏ qua `relationship_type` → điểm số tổng hợp + hạng chữ.
- **v2**: gửi `relationship_type` → phân tích định tính theo mục đích quan hệ (tiêu chí có trọng số, kết luận, luận giải, lời khuyên).

**Định dạng ngày sinh:** `dd/mm/yyyy` (ví dụ `15/05/1990`). Khác với một số endpoint khác trong tài liệu này dùng ISO — riêng Hợp Tuổi dùng parser `dd/mm/yyyy`.

## Request

```json
{
  "person1_birth_date": "15/05/1990",
  "person1_birth_time": 8,
  "person1_gender": 1,
  "person2_birth_date": "20/03/1992",
  "person2_birth_time": 10,
  "person2_gender": -1,
  "relationship_type": "PHU_THE"
}
```

| Field | Required | Type | Validation / ghi chú |
|---|---|---|---|
| person1_birth_date | Yes | string | `dd/mm/yyyy`, quá khứ, năm ≥ 1900 |
| person2_birth_date | Yes | string | Cùng quy tắc |
| person1_birth_time | No | int \| null | Giờ sinh dropdown Tứ Trụ: `0, 2, 4, 6, 8, 10, 11, 14, 16, 18, 20, 22, 23` |
| person2_birth_time | No | int \| null | Cùng tập giá trị |
| person1_gender | No | int \| null | `1` (nam) hoặc `-1` (nữ); dùng cho v2 **Phu Thê** (tiêu chí giới tính) |
| person2_gender | No | int \| null | Cùng quy tắc |
| relationship_type | No | string \| null | Bỏ trống → **v1**. Có giá trị → **v2**; phải là một trong bảng dưới |

### `relationship_type` (v2)

| Giá trị | Nhãn hiển thị | Đối xứng |
|---|---|---|
| PHU_THE | Phu Thê | Có |
| DOI_TAC | Đối Tác | Có |
| SEP_NHAN_VIEN | Sếp — Nhân Viên | Không (người 1 = người hỏi / sếp) |
| DONG_NGHIEP | Đồng Nghiệp | Có |
| BAN_BE | Bạn Bè | Có |
| PHU_TU | Phụ Tử | Không (người 1 = cha mẹ) |
| ANH_CHI_EM | Anh Chị Em | Có |
| THAY_TRO | Thầy — Trò | Không (người 1 = thầy) |

**Ghi chú vai trò (v2, quan hệ không đối xứng):** `person1` luôn là **người hỏi** (sếp, thầy, hoặc phụ huynh tùy loại). `person2` là đối tượng còn lại.

## Response 200 — v1 (`relationship_type` không gửi)

```json
{
  "status": "success",
  "version": 1,
  "person1": {
    "birth_date": "1990-05-15",
    "menh": "Lộ Bàng Thổ",
    "hanh": "Thổ",
    "nhatChu": "Đinh Hỏa",
    "gender": 1
  },
  "person2": { "...": "..." },
  "overall_score": 72,
  "grade": "B",
  "ngu_hanh_relation": "Tương Sinh",
  "details": [
    {
      "category": "Ngũ Hành Nạp Âm",
      "score": 90,
      "description": "Thổ và Kim — Tương Sinh."
    }
  ],
  "summary": "...",
  "advice": "..."
}
```

| Field | Mô tả |
|---|---|
| version | Luôn `1` |
| person1 / person2 | `birth_date` trả về dạng ISO (`YYYY-MM-DD`); không gồm chỉ số nội bộ engine |
| gender | Chỉ có khi client gửi `person*_gender` |
| overall_score | Trung bình điểm các hạng mục v1 |
| grade | `A` \| `B` \| `C` \| `D` |
| details | Ngũ Hành Nạp Âm, Nhật Chủ, Địa Chi, Thiên Can |

## Response 200 — v2 (`relationship_type` có giá trị)

```json
{
  "status": "success",
  "version": 2,
  "relationship_type": "PHU_THE",
  "relationship_label": "Phu Thê",
  "person1": {
    "birth_date": "1990-05-15",
    "menh": "Lộ Bàng Thổ",
    "hanh": "Thổ",
    "nhatChu": "Đinh Hỏa",
    "gender": 1
  },
  "person2": { "...": "..." },
  "verdict": "Tương hợp",
  "verdict_level": 2,
  "criteria": [
    {
      "name": "Ngũ Hành Nạp Âm",
      "sentiment": "positive",
      "description": "..."
    }
  ],
  "reading": "...",
  "advice": "..."
}
```

| Field | Mô tả |
|---|---|
| version | Luôn `2` |
| verdict | Nhãn kết luận tiếng Việt (ví dụ `Rất tương hợp`, `Tương hợp`, `Cần lưu ý`, `Nhiều thử thách`) |
| verdict_level | `1` (tốt nhất) … `4` (khó khăn nhất) — map với `verdict` |
| criteria | Mỗi phần tử: `name` (nhãn tiêu chí), `sentiment` (`positive` \| `neutral` \| `negative`), `description` (giải thích) |
| reading / advice | Chuỗi luận giải và gợi ý; nội dung gốc lấy từ `docs/seed/hop-tuoi-readings.json` và ngữ cảnh từ các tiêu chí |

### Tiêu chí v2 theo `relationship_type` (tên `name` trong `criteria`)

Các tiêu chí sau xuất hiện theo đúng thứ tự và trọng số trong engine (`src/engine/hop_tuoi.py`); bảng này để client biết trước có những mục nào.

| relationship_type | Các key tiêu chí (theo thứ tự) |
|---|---|
| PHU_THE | nap_am, luc_hop, tam_hop, dia_chi_xung, thien_can, nhat_chu, thap_than_spouse, phu_the_gioi_tinh |
| DOI_TAC | nap_am, nhat_chu, dung_than_bo_tro, dia_chi_xung, thien_can |
| SEP_NHAN_VIEN | nap_am_directed, nhat_chu_directed, cuong_nhuoc_pair, thien_can_directed |
| DONG_NGHIEP | nhat_chu, dia_chi_xung, thien_can, nap_am |
| BAN_BE | dia_chi_harmony, nap_am, nhat_chu |
| PHU_TU | nap_am_directed, dia_chi_xung, thien_can_directed |
| ANH_CHI_EM | nap_am, dia_chi_xung, nhat_chu |
| THAY_TRO | nhat_chu_directed, dung_than_bo_tro, cuong_nhuoc_pair |

**Lưu ý:**

- `thap_than_spouse`, `dung_than_bo_tro`, `cuong_nhuoc_pair` cần **đủ** `birth_time` hai người (có Tứ Trụ); thiếu giờ → tiêu chí đó thường trả `neutral` với mô tả “cần giờ sinh…”.
- `phu_the_gioi_tinh` (Phu Thê): cần **cả** `person1_gender` và `person2_gender` (`1` / `-1`) mới phân loại tích cực theo cặp nam/nữ truyền thống; thiếu một bên hoặc cùng mã giới → `neutral`.

## Error Responses (Hợp Tuổi)

| HTTP | error_code | When |
|---|---|---|
| 400 | INVALID_INPUT | Sai định dạng ngày, giờ, giới, `relationship_type` không hợp lệ, v.v. |
| 401 | UNAUTHORIZED | Thiếu / sai API key |
| 429 | RATE_LIMITED | Vượt hạn mức |
| 500 | INTERNAL_ERROR | Lỗi máy chủ |
