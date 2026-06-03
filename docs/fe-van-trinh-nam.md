# FE Integration — Bài luận Vận trình năm (Lưu niên + Lưu nguyệt)

Tài liệu dành cho **FE / NLTT**: cách gọi API để dựng bài **Vận trình năm {year}** — luận **Lưu niên** (cả năm), **12 Lưu nguyệt** (từng tháng), và **Lưu nhật** (lịch ngày trong tháng).

Đọc cùng:

- `docs/api-spec.md` — contract `GET /v1/luu-nien/luan-context`
- `docs/van-trinh-nam-outline.md` — dàn bài editorial (A→B→C→D)
- `docs/fixtures/direction-c/van-trinh-nam-luan-context-2026.json` — response mẫu

---

## 1. Endpoint chính — gọi một lần cho cả bài

```
GET /v1/luu-nien/luan-context
```

| Param | Bắt buộc | Ghi chú |
|--------|----------|---------|
| `year` | ✓ | Năm dương (1900–2100), vd. `2026` |
| `birth_date` | ✓ | `dd/mm/yyyy` |
| `birth_time` | ✓ | Enum Tứ Trụ: `0,2,4,6,8,10,11,14,16,18,20,22,23` |
| `gender` | ✓ | `1` nam · `-1` nữ |
| `tz` | | IANA timezone (validate ngày sinh) |

**Ví dụ:**

```http
GET /v1/luu-nien/luan-context?year=2026&birth_date=15/03/1984&birth_time=8&gender=1
```

- Response ~30KB; cold compute ~100ms (p95 SLA API: 1s).
- BE cache Redis 60 ngày: `van-trinh-nam-luan:{profile_hash}:{year}:{engine_version}`.
- FE nên cache client theo cùng key logic: `profileHash + year + meta.engine_version`.

---

## 2. Phân vai endpoint — dùng cái nào khi nào

| Mục đích | Endpoint | Dùng cho bài luận? |
|----------|----------|-------------------|
| **Bài năm đầy đủ** (A→B→C→D + LLM) | `GET /v1/luu-nien/luan-context` | **Có — endpoint chính** |
| Card/preview nhanh (đã có prose) | `GET /v1/la-so/luu-nien` | Chỉ UI teaser/paywall, **không** feed LLM bài dài |
| Lá số + personality | `GET /v1/la-so` | Bổ sung màn intro (optional) |
| Lịch tháng chi tiết (31 ngày) | `GET /v1/lich-thang` | Drill-down khi user bấm vào tháng |
| Chi tiết 1 ngày | `GET /v1/chon-ngay/day-detail` | Từ `b3.best_days` / `avoid_days` |
| Tiểu vận tháng (stub) | `GET /v1/tieu-van` | **Deprecated** — không dùng cho sản phẩm mới |

**Quy tắc:** Bài luận dài = **1 call `luan-context`**. Các endpoint khác chỉ phục vụ preview, navigation, hoặc deep-link.

---

## 3. Luồng FE đề xuất

```
Profile + năm
    → GET /v1/luu-nien/luan-context
        → [Có LLM]  payload + writing_brief → NLTT → prose theo render_order
        → [MVP UI]  map part_a / part_b / part_d trực tiếp
    → b3 best/avoid day click → GET day-detail hoặc màn chọn ngày
```

1. User chọn **năm** + **profile** (ngày/giờ sinh, giới tính).
2. Gọi **`luan-context`** một lần.
3. **Có LLM:** gửi JSON (hoặc subset) + `writing_brief` cho NLTT; nhận prose theo `writing_brief.render_order`.
4. **Không LLM (MVP):** render `fact_bullets_vi`, lịch `b3`, tag signals; phần câu văn để LLM sau.
5. Deep-link: ngày trong `b3` → `day-detail?date=YYYY-MM-DD&...`.

---

## 4. Map response → dàn bài editorial

Theo `writing_brief.render_order` và `docs/van-trinh-nam-outline.md`.

### Phần A — Lưu niên (cả năm)

| Block UI | Path API | FE / LLM làm gì |
|----------|----------|-----------------|
| **A1 Hook năm** | `part_a.hook_year` | Viết từ `year_theme_signal`, `fact_bullets_vi`, `year_can_chi`, `year_hanh` |
| **A2 Bạn trong năm** | `part_a.you_this_year` | `natal_facts_vi`, `nhat_chu_hanh`, `dung_than`, `ky_than`, `dai_van` |
| **A3 Bốn mảng năm** | `part_a.four_aspects_year` | 4 item: `su_nghiep`, `tai_loc`, `tinh_cam`, `suc_khoe` |
| Thứ tự ưu tiên | `part_a.year_aspect_ranking` | Mảng nào nói trước / dài hơn |

**Mỗi aspect (A3):**

```json
{
  "aspect_id": "tinh_cam",
  "label_vi": "Tình cảm",
  "verdict_signal": "than_trong",
  "driver_tags": ["flow_year_xung_tuoi"],
  "fact_bullets_vi": ["..."],
  "timing_tags": []
}
```

| Field | Ý nghĩa |
|-------|---------|
| `verdict_signal` | `thuan` · `than_trong` · `can_nang` — map sang copy UI/LLM |
| `driver_tags` | Gợi ý góc luận — **không** hiện raw cho user cuối |
| `fact_bullets_vi` | Facts atomic cho LLM |
| `tinh_cam` | Tương đương `life_areas.tinh_duyen` ở endpoint card MVP |

**Đại vận đổi trong năm** (`part_a.you_this_year.dai_van.transition_in_year`):

```json
{
  "from_display": "Nhâm Ngọ",
  "to_display": "Quý Mùi",
  "applies_from_month": 4
}
```

→ Từ tháng `applies_from_month` trở đi: nhắc “giai đoạn lớn chuyển”.

---

### Phần B — 12 Lưu nguyệt (từng tháng)

`part_b.luu_nguyet_months` — **đúng 12 phần tử**, tháng dương `month_num` 1→12.

| Block | Path | Ghi chú |
|-------|------|---------|
| **B1 Chủ đề tháng** | `b1_month_theme` | `month_archetype`, `luu_nguyet_display`, `element_relation_nhat_chu` |
| **B2 Mảng nổi bật** | `b2_month_emphasis` | **≤ 2** mảng; `emphasis_signal`: `up` / `down` / `neutral` |
| **B3 Lưu nhật** ★ | `b3_luu_nhat_calendar` | `best_days[3]`, `avoid_days[3]`, `top_hours[]` |
| **B4 Nên / Tránh** | `b4_action` | `action_tags_nen[]`, `action_tags_tranh[]` |
| QA độ dài | `qa_hints.target_word_band` | `[80, 120]` từ/tháng cho LLM |

**`month_archetype` → copy ngôn ngữ đời:**

| Signal | Ý editorial |
|--------|-------------|
| `nang_do` | Tháng đẩy mạnh, chủ động |
| `gieo_hat` | Bắt đầu, gieo hạt |
| `thu_hoach` | Hoàn tất, thu hoạch |
| `phong_thu` | Phòng thủ, ổn định |
| `chuyen_dong` | Biến động, linh hoạt |

**B3 — moat sản phẩm:** render trực tiếp `date_vi`, `can_chi`, `grade`, `score`. Ngày hạn có `mitigation_tags` → LLM **bắt buộc** kèm gợi ý hóa giải (rule G2).

**Rule chống lặp (quan trọng):**

- 4 mảng (`su_nghiep`, `tai_loc`, `tinh_cam`, `suc_khoe`) luận **sâu một lần ở Phần A**.
- Ở cấp tháng: chỉ nói **mảng nào sống dậy** (`b2`, ≤2 item), không lặp đủ 4 mảng × 12 tháng.

---

### Phần C — Kết bài

`part_c.closing_hints.synthesis_inputs`:

| Field | Dùng để |
|-------|---------|
| `archetype_counts` | Tóm kiểu tháng chiếm ưu thế trong năm |
| `strong_months[]` | Tháng mạnh — LLM viết 3 xu hướng / câu mang theo |

FE/LLM viết Phần C từ đây; không bịa thêm facts.

---

### Phần D — Mechanics (gập)

`part_d.mechanics` — Tứ trụ, Dụng/Kỵ, Đại vận, Lưu niên mẫu.

UI: accordion / “Xem thuật ngữ” — **không** nhét vào prose Phần A/B.

---

## 5. Contract LLM — bắt buộc

### Không dùng prose từ BE (bài signal-based)

Response **không có** các key sau (và LLM **không** copy từ card MVP):

- `verdict_vi`
- `delta_vs_year_vi`
- `giai_hoa_goi_y_vi`
- `year_theme_vi`

Danh sách đầy đủ: `writing_brief.forbidden_response_keys`.

### Dùng signals thay prose

| Thay vì | Dùng |
|---------|------|
| “Thuận / Cần thận trọng” (câu có sẵn) | `verdict_signal`, `emphasis_signal` |
| Câu theme năm | `year_theme_signal` + LLM diễn giải |
| Lý do kỹ thuật | `driver_tags`, `shift_tags`, `mitigation_tags` |
| Hành động nên/tránh | `action_tags_nen`, `action_tags_tranh` |

### Prompt pack gửi NLTT

```json
{
  "writing_brief": "<from response.writing_brief>",
  "facts": {
    "part_a": "...",
    "part_b": "...",
    "part_c": "...",
    "part_d": "..."
  },
  "rules": "Tuân G1–G8 trong writing_brief.rules; 4 mảng chỉ ở A3; mỗi tháng ≤2 emphasis; mỗi tháng có b3 lịch ngày"
}
```

**Thứ tự render** (`writing_brief.render_order`):

1. `A1_hook_year`
2. `A2_you_this_year`
3. `A3_four_aspects_year`
4. `B_luu_nguyet_months` (loop 12)
5. `C_closing`
6. `D_mechanics_collapsed`

---

## 6. Endpoint phụ — drill-down

### Preview / paywall (không thay `luan-context`)

```http
GET /v1/la-so/luu-nien?year=2026&birth_date=15/03/1984&birth_time=8&gender=1
```

- Có sẵn `year_theme_vi`, `life_areas[].verdict_vi` — **chỉ** cho card/teaser trước paywall.
- `month_score_values[12]` — biểu đồ 12 tháng MVP (thang **âm lịch**; khác granularity `part_b` dương lịch).

### Lịch tháng đầy đủ

```http
GET /v1/lich-thang?year=2026&month=4&birth_date=15/03/1984&birth_time=8&gender=1
```

- 31 ngày + score/grade — khi user mở “xem full lịch tháng 4”.
- Scoring **cùng engine** với `b3` trong `luan-context`.

### Chi tiết một ngày

```http
GET /v1/chon-ngay/day-detail?date=2026-04-20&birth_date=15/03/1984&birth_time=8&gender=1&intent=MAC_DINH
```

- Deep-link từ `b3.best_days[].date` hoặc `avoid_days[].date`.

---

## 7. UI states & disclaimer

| Việc | Gợi ý |
|------|--------|
| Loading | Skeleton Phần A (1 block) + Phần B (12 accordion) |
| Cache invalidation | `meta.engine_version` đổi → refetch |
| Disclaimer | Hiện footnote từ `meta.disclaimers` |
| `luu_nguyet_pillar_solar_simplified` | Lưu nguyệt v1 dùng quy tắc tháng dương đơn giản — ghi chú nếu cần |
| `not_medical_or_legal_advice` | Disclaimer y tế/pháp lý/tài chính |
| Lỗi 400 | `birth_date` tương lai / thiếu param / `birth_time` sai enum |
| Lỗi 500 | Retry; hiếm khi invariant 12 tháng fail |

---

## 8. Anti-patterns

1. Gọi `la-so/luu-nien` rồi paste `verdict_vi` vào bài dài — trùng/sai contract signal.
2. Loop 12 lần `tieu-van` — deprecated, không có lịch lưu nhật.
3. Luận đủ 4 mảng ở **mỗi tháng** — sai rule A1/A2; tháng chỉ có `b2` ≤2 mảng.
4. Bỏ `b3` ở tháng êm — mỗi tháng **phải** có lịch ngày (moat sản phẩm).
5. Hiện `driver_tags` / `shift_tags` raw cho user — chỉ dùng nội bộ LLM.

---

## 9. Checklist tích hợp

- [ ] Màn “Vận trình năm {year}”: 1 request `GET /v1/luu-nien/luan-context`
- [ ] LLM nhận `writing_brief` + `part_a` / `part_b` / `part_c`
- [ ] Render 12 tháng theo `b1`→`b4`; accordion + anchor `#thang-4`
- [ ] Click ngày `b3` → `day-detail` hoặc màn chọn ngày
- [ ] `part_d` collapsed; disclaimer từ `meta.disclaimers`
- [ ] Teaser trước paywall: optional `GET /v1/la-so/luu-nien`
- [ ] Không dùng `GET /v1/tieu-van` cho sản phẩm mới

---

## Tóm tắt

| Tầng Bát Tự | Nguồn trong API |
|-------------|-----------------|
| Lưu niên (năm) | `part_a` |
| Lưu nguyệt (tháng) | `part_b.luu_nguyet_months[]` |
| Lưu nhật (ngày) | `part_b.*.b3_luu_nhat_calendar` |
| Đại vận | `part_a.you_this_year.dai_van` + `part_d.mechanics` |

**Một endpoint, một lần gọi:** `GET /v1/luu-nien/luan-context`. BE trả facts + signals; FE/LLM viết prose theo `writing_brief`.
