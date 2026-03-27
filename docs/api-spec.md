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
- `birth_time` provided → trả đầy đủ Tứ Trụ, Dụng Thần, Thập Thần, **`element_counts`** (trọng số ngũ hành — cùng nguồn với `GET /v1/la-so` → `_raw.element_counts`) và **`support_ratio`** (0–1). Để hiển thị %: chia mỗi hành cho tổng các trọng số rồi nhân 100.
- `gender` provided (+ birth_time) → thêm Đại Vận (10-year luck cycles)
- `birth_year_can_chi` và `menh` (Nạp Âm) tính theo **năm Can Chi Bát Tự** (ranh giới **Lập Xuân**, cùng quy ước trụ Năm trong Tứ Trụ): sinh trước Lập Xuân vẫn thuộc năm Can Chi của năm dương lịch trước.

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
  "element_counts": {
    "Kim": 1.2,
    "Mộc": 2.0,
    "Thủy": 2.5,
    "Hỏa": 0.8,
    "Thổ": 1.5
  },
  "support_ratio": 0.38,
  "chart_strength": "nhược",
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

# API Spec — GET /v1/la-so

Lá số **diễn giải có cấu trúc**: cùng nguồn tính toán với Tứ Trụ (`get_tu_tru`, cường nhược, Dụng Thần, Thập Thần, Đại Vận) nhưng trả object đã gắn **nhãn ngữ nghĩa** (archetype Nhật Chủ, gợi ý sự nghiệp/tài/sức khỏe, tín hiệu tình duyên…) để App hoặc Supabase Edge Function đưa vào LLM tạo văn xuôi. **Không** gọi LLM trong API này.

**Khác POST /v1/tu-tru:** `birth_time` **bắt buộc** (không đủ trụ thì không diễn giải). `gender` tuỳ chọn: có `1` / `-1` thì thêm `tinh_duyen` và `dai_van_current`.

## Request (query)

| Param | Required | Type | Description |
|---|---|---|---|
| birth_date | Yes | string | `dd/mm/yyyy`, quá khứ, năm ≥ 1900 |
| birth_time | Yes | int | Giờ sinh (dropdown giống Tứ Trụ) |
| gender | No | int | `1` nam \| `-1` nữ |

## Response 200 (rút gọn — cấu trúc chính)

```json
{
  "status": "success",
  "birth_date": "1990-05-15",
  "birth_time": 8,
  "gender": 1,
  "tinh_cach": {
    "archetype": "Ngọn nến",
    "image": "...",
    "core_traits": ["..."],
    "element": "Hỏa",
    "polarity": "Âm",
    "strength": "vượng",
    "strength_note": "..."
  },
  "su_nghiep": {
    "dominant_thap_than": "Chính Tài",
    "dominant_thap_than_key": "chinh_tai",
    "career_tendency": "...",
    "suitable_fields": ["..."],
    "wealth_style": "...",
    "wealth_risk": "...",
    "dung_than_element": "Thủy",
    "element_tip": "..."
  },
  "tai_van": {
    "wealth_style": "...",
    "wealth_risk": "...",
    "dung_than": "Thủy",
    "hi_than": "Kim",
    "ky_than": "Thổ"
  },
  "suc_khoe": {
    "dm_element": "Hỏa",
    "dm_strength": "vượng",
    "organ": "...",
    "risk_when_weak": "...",
    "risk_when_strong": "...",
    "health_context": "risk_when_strong",
    "boost_element": "Thủy",
    "avoid_element": "Thổ"
  },
  "tinh_duyen": {
    "spouse_star": "Chính Tài (vợ)",
    "spouse_presence": 0,
    "affair_presence": 0,
    "dm_strength": "vượng",
    "signals": {
      "strong_spouse": false,
      "multiple_affair": false,
      "weak_dm_needs_support": false,
      "strong_dm_dominant": true
    }
  },
  "dai_van_current": {
    "display": "Giáp Thân",
    "hanh": "Mộc",
    "nap_am_hanh": "Thủy",
    "age_range": "28-37"
  },
  "_raw": {
    "tu_tru_display": "...",
    "element_counts": {},
    "support_ratio": 0.0,
    "thap_than_profile": { "year": "...", "month": "...", "hour": "..." },
    "god_counts": {}
  }
}
```

- `tinh_duyen` và `dai_van_current` chỉ có khi client gửi `gender`.
- `_raw` dùng thêm ngữ cảnh kỹ thuật cho bước LLM (không bắt buộc hiển thị user).

## Error Responses (Lá số)

| HTTP | error_code | When |
|---|---|---|
| 400 | INVALID_INPUT | Thiếu/thời gian không hợp lệ, `birth_time` sai enum |
| 401 | UNAUTHORIZED | API key |
| 429 | RATE_LIMITED | Quota |
| 500 | INTERNAL_ERROR | Lỗi máy chủ |

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

---

# API Spec — GET /v1/phong-thuy

Gợi ý phong thủy theo Dụng Thần / Kỵ Thần (hướng, màu, số, vật phẩm), tùy **mục đích** không gian; **version 2** thêm Phi Tinh năm, cá nhân hóa lá số (khi có giờ sinh), và hóa giải cặp đôi (khi có `partner_birth_date`).

**Định dạng ngày:** `dd/mm/yyyy` (giống Hợp Tuổi), qua `parse_dmy`.

## Request (query)

| Param | Required | Type | Description |
|---|---|---|---|
| birth_date | Yes | string | Ngày sinh chủ `dd/mm/yyyy`, quá khứ, năm ≥ 1900 |
| birth_time | No | int | Một trong giờ dropdown engine (xem Tứ Trụ); có → Dụng/Kỵ từ Tứ Trụ + block `personalization` nếu khớp điều kiện |
| gender | No | int | `1` (nam) hoặc `-1` (nữ) — dự phòng, chưa dùng trong logic phong thủy |
| tz | No | string | IANA, mặc định `Asia/Ho_Chi_Minh` — so sánh “quá khứ” với “hôm nay” |
| purpose | No | string | `NHA_O` \| `VAN_PHONG` \| `CUA_HANG` \| `PHONG_KHACH` (mặc định `NHA_O`) |
| year | No | int | 1900–2100; nếu có → thêm block **Phi Tinh** lưu niên cho năm dương lịch đó |
| partner_birth_date | No | string | `dd/mm/yyyy` quá khứ; nếu có (và không chỉ khoảng trắng) → có thể thêm `couple_harmony` khi hai Nạp Âm **tương khắc trực tiếp** |

## Response 200 — version 2 (rút gọn)

```json
{
  "status": "success",
  "version": 2,
  "purpose": "NHA_O",
  "user_menh": { "hanh": "Kim", "name": "Hải Trung Kim" },
  "dung_than": "Thổ",
  "ky_than": "Hỏa",
  "huong_tot": ["Đông Bắc", "Tây Nam"],
  "huong_xau": [{ "huong": "Nam", "ly_do": "..." }],
  "mau_may_man": ["Vàng đất", "Nâu"],
  "mau_ky": ["Đỏ"],
  "so_may_man": [2, 5, 8],
  "so_ky": [7],
  "vat_pham": [{ "item": "...", "element": "...", "placement": "...", "reason": "..." }],
  "purpose_specific": { "huong_giuong": { "tot": "...", "ly_do": "..." } },
  "personalization": { "chart_strength": "nhược", "intensity": "vừa", "note": "...", "extra_items": [] },
  "phi_tinh_year": 2026,
  "phi_tinh": [
    {
      "direction": "Đông Nam",
      "star": 4,
      "star_name": "Tứ Lục Văn Xương",
      "hanh": "Mộc",
      "nature": "tốt",
      "meaning": "..."
    }
  ],
  "huong_tot_nam_nay": ["Đông Nam"],
  "huong_xau_nam_nay": ["Tây"],
  "hoa_giai": [{ "direction": "Tây", "star": 3, "remedy": "..." }],
  "phi_tinh_note_vi": "...",
  "couple_harmony": {
    "person1_hanh": "Mộc",
    "person2_hanh": "Thổ",
    "person1_menh_name": "Đại Lâm Mộc",
    "person2_menh_name": "Lộ Bàng Thổ",
    "relation": "Tương Khắc (Mộc khắc Thổ)",
    "remedy_element": "Hỏa",
    "explanation": "...",
    "remedies": ["..."],
    "colors_for_shared_space": ["..."]
  }
}
```

| Field | Mô tả |
|---|---|
| version | Luôn `2` cho contract hiện tại |
| purpose_specific | Chỉ khi seed mục đích có thêm khóa (ví dụ hướng giường, quầy) |
| personalization | Chỉ khi có `birth_time` và engine tính được cường nhược |
| phi_tinh* / hoa_giai | Chỉ khi gửi `year` |
| couple_harmony | Chỉ khi có `partner_birth_date` hợp lệ **và** hai người có quan hệ khắc trực tiếp theo ngũ hành Nạp Âm |

### Phi Tinh — giả định API (quan trọng cho client)

- **Năm & nhập trung:** Dùng **năm dương lịch** `year`. Nhập trung mặc định: neo 2024 = 3, bước −1/năm (mod 9); có thể ghi đè trong `docs/seed/phi-tinh-year-center.json` (chỉ số 1–9). Override **chỉ** đổi trung tinh; thuận/nghịch phi vẫn theo can **Gregorian** của `year`.
- **Thuận / nghịch:** `(year - 4) % 10` chẵn → Dương can (phi thuận), lẻ → Âm can (phi nghịch). **Không** theo Lập Xuân hay đổi năm âm lịch — có thể không khớp mọi sách.
- **huong_tot_nam_nay / huong_xau_nam_nay:** Theo `nature` sao trong `phi-tinh-stars.json`, **không** lọc theo Dụng Thần người dùng. Chi tiết trong `phi_tinh_note_vi`.
- **Override vs thuận/nghịch:** Nếu JSON override lệch so với bảng bạn tin, có thể ra lưới khác tài liệu — xem `_comment` trong `phi-tinh-year-center.json`.

## Error Responses (Phong thủy)

| HTTP | error_code | When |
|---|---|---|
| 400 | INVALID_INPUT | Ngày/giờ/giới/purpose không hợp lệ |
| 500 | INTERNAL_ERROR | Lỗi máy chủ; nếu thiếu/hỏng `phi-tinh-stars.json` khi gọi kèm `year`, có thể trả `message`/`message_en` mô tả lỗi seed Phi Tinh |
