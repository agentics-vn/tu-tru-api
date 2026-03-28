# Critical Test Cases — SME Sign-off Required

Run: `npm run test:tc`
All 10 must pass before production deployment.

---

## TC-01 — Basic happy path
- **Input:** birth_date: 1990-05-15, intent: CUOI_HOI, range: 2026-02-01 to 2026-04-30
- **Expect:** `recommended_dates` has >= 1 entry with grade A or B
- **Rationale:** Year 1990 = Canh Ngọ → Mệnh Thổ. Check scoring works end-to-end.

## TC-02 — Xung day NEVER in recommended
- **Input:** birth_date: 1990-05-15 (Canh Ngọ year, Chi=Ngọ=index 6), intent: MAC_DINH, range: 90 days
- **Expect:** Zero days with Chi=Tý (index 0, Xung of Ngọ) in `recommended_dates`
- **Rationale:** Layer 2 must catch all Tý days for Ngọ year people.

## TC-03 — Nguyệt Kỵ filtered
- **Input:** Any birth_date, intent: MAC_DINH, range includes a lunar day 5
- **Expect:** That date NOT in `recommended_dates`. Present in `dates_to_avoid` OR simply absent.

## TC-04 — Tháng Cô Hồn (CUOI_HOI)
- **Input:** birth_date: 1985-01-01, intent: CUOI_HOI, range_start: 2026-08-20, range_end: 2026-09-15
  - Note: This range covers lunar month 7 (Cô Hồn 2026 ≈ Aug 25 – Sep 22 solar)
- **Expect:** All days inside lunar month 7 appear in `dates_to_avoid` with severity 3, OR `NO_DATES_FOUND` error.

## TC-05 — Range too large
- **Input:** range_start: 2026-01-01, range_end: 2026-04-02 (91 days)
- **Expect:** HTTP 400, error_code: RANGE_TOO_LARGE

## TC-06 — Invalid intent
- **Input:** intent: "BAO_GIO_CUNG_DUOC"
- **Expect:** HTTP 400, error_code: INVALID_INPUT

## TC-07 — Không cần API key
- **Input:** Valid body, không gửi `X-API-Key`
- **Expect:** HTTP 200 (hoặc 4xx nghiệp vụ khác), **không** được 401 vì thiếu key

## TC-08 — (Đã bỏ) Rate limit theo API key
- Trước đây: giới hạn theo key. Ứng dụng không còn middleware API key / rate limit trong process — nếu cần hạn mức, đặt tại gateway (CDN, API gateway, Fly proxy).

## TC-09 — top_n respected
- **Input:** top_n: 1, range: 90 days, any birth/intent
- **Expect:** `recommended_dates` array has exactly 1 item

## TC-10 — Deterministic output
- **Input:** Same request body, run 3 times
- **Expect:** Identical `recommended_dates` in all 3 responses (same dates, same scores, same order)
- **Rationale:** Validates all engine functions are pure (no randomness, no time-based variance)

---

## SME Verification Checklist
Before sign-off, SME must also manually verify:
- [ ] TC-01 recommended dates are genuinely auspicious per traditional almanac
- [ ] TC-02 no Xung date appears (check Chi index math)
- [ ] TC-04 Ghost Month handled correctly
- [ ] At least 3 additional dates from `recommended_dates` cross-checked against physical lịch vạn niên
