# Algorithm Reference — Bat Tu Date Selection Engine

> Source of truth for all calculations. Claude Code must implement exactly as specified here.
> All tables are verified against traditional Vietnamese almanac (lịch vạn niên).

---

## 1. CAN CHI LOOKUP TABLES

### 1.1 Thiên Can (Heavenly Stems) — index 0–9
```
index: 0     1     2      3      4     5     6      7      8      9
can:   Giáp  Ất    Bính   Đinh   Mậu   Kỷ    Canh   Tân    Nhâm   Quý
hanh:  Mộc   Mộc   Hỏa    Hỏa    Thổ   Thổ   Kim    Kim    Thủy   Thủy
am_duong: D  Â    D      Â      D     Â     D      Â      D      Â
```
(D = Dương, Â = Âm)

### 1.2 Địa Chi (Earthly Branches) — index 0–11
```
index: 0    1     2     3     4      5    6     7     8      9     10     11
chi:   Tý   Sửu   Dần   Mão   Thìn   Tỵ   Ngọ   Mùi   Thân   Dậu   Tuất   Hợi
hanh:  Thủy Thổ   Mộc   Mộc   Thổ    Hỏa  Hỏa   Thổ   Kim    Kim   Thổ    Thủy
```

### 1.3 Địa Chi Tương Xung (Direct Conflict pairs — severity 3 in Layer 2)
```
Tý(0)   ↔  Ngọ(6)
Sửu(1)  ↔  Mùi(7)
Dần(2)  ↔  Thân(8)
Mão(3)  ↔  Dậu(9)
Thìn(4) ↔  Tuất(10)
Tỵ(5)   ↔  Hợi(11)
```
isXung(a, b) = Math.abs(a - b) === 6

### 1.4 Thiên Can Tương Khắc (Stem Conflict — severity 2 in Layer 2)
```
Giáp(0) khắc Mậu(4)    |   Mậu(4)  khắc Nhâm(8)
Ất(1)   khắc Kỷ(5)     |   Kỷ(5)   khắc Quý(9)
Bính(2) khắc Canh(6)   |   Canh(6) khắc Giáp(0)
Đinh(3) khắc Tân(7)    |   Tân(7)  khắc Ất(1)
Nhâm(8) khắc Bính(2)   |   Quý(9)  khắc Đinh(3)
```
isCanKhac(a, b): check lookup map above (not symmetric — Giáp khắc Mậu ≠ Mậu khắc Giáp)

---

## 2. GETCANCHIDAY() — Day Pillar Calculation

### Algorithm
```javascript
function getJDN(year, month, day) {
  // Julian Day Number (integer, noon UT)
  const a = Math.floor((14 - month) / 12)
  const y = year + 4800 - a
  const m = month + 12 * a - 3
  return day
    + Math.floor((153 * m + 2) / 5)
    + 365 * y
    + Math.floor(y / 4)
    - Math.floor(y / 100)
    + Math.floor(y / 400)
    - 32045
}

// Anchor: 1900-01-31 = Giáp Tý (JDN = 2415051)
const ANCHOR_JDN = 2415051

function getCanChiDay(dateString) {
  // dateString: "YYYY-MM-DD"
  const [y, m, d] = dateString.split('-').map(Number)
  const jdn = getJDN(y, m, d)
  const offset = jdn - ANCHOR_JDN
  const canIndex = ((offset % 10) + 10) % 10
  const chiIndex = ((offset % 12) + 12) % 12
  return { canIndex, chiIndex, can: CAN[canIndex], chi: CHI[chiIndex] }
}
```

### Verified Test Vectors (machine-verified ✅ — do NOT change these)
```
Date          Result      Notes
1900-01-31    Giáp Tý     Anchor — offset 0
1900-02-01    Ất Sửu      Anchor + 1
2000-01-01    Mậu Dần     offset=36494, mod10=4(Mậu), mod12=2(Dần)
2024-01-01    Giáp Thân   offset=45260, mod10=0(Giáp), mod12=8(Thân)
2024-02-10    Giáp Tý     Mồng 1 Tết Giáp Thìn 2024
2025-01-29    Mậu Ngọ     Mồng 1 Tết Ất Tỵ 2025
2026-01-17    Tân Hợi     Mồng 1 Tết Bính Ngọ 2026
```
**Algorithm verified programmatically. SME spot-check 2–3 dates against physical lịch vạn niên.**

---

## 3. NGŨ HÀNH MỆnh — 60 HOA GIÁP TABLE

The Mệnh (Destiny Element) is determined by the year's Can + Chi using Nạp Âm method.
This is NOT the same as the element of the Can or Chi individually.

**Ranh giới năm (Bát Tự):** Can Chi **năm** dùng cho Nạp Âm mệnh phải trùng năm trụ trong Tứ Trụ — tức sau **Lập Xuân** (tiết khí ~4–5/2) mới đổi sang năm dương lịch mới; trước đó vẫn thuộc năm Can Chi của năm dương lịch trước. API: `get_menh_nap_am_from_date(y,m,d)`; `get_menh_nap_am(year)` chỉ là shortcut theo số năm (không dùng cho sinh đầu năm).

### Complete 60 Hoa Giáp → Ngũ Hành Mệnh
```javascript
// Key: "can_index-chi_index", Value: ngu_hanh_menh
const NAP_AM = {
  // Hải Trung Kim (Gold in the Sea)
  "0-0": "Kim",  // Giáp Tý
  "1-1": "Kim",  // Ất Sửu

  // Lô Trung Hỏa (Fire in the Furnace)
  "2-2": "Hỏa",  // Bính Dần
  "3-3": "Hỏa",  // Đinh Mão

  // Đại Lâm Mộc (Great Forest Wood)
  "4-4": "Mộc",  // Mậu Thìn
  "5-5": "Mộc",  // Kỷ Tỵ

  // Lộ Bàng Thổ (Roadside Earth)
  "6-6": "Thổ",  // Canh Ngọ
  "7-7": "Thổ",  // Tân Mùi

  // Kiếm Phong Kim (Sword Metal)
  "8-8": "Kim",  // Nhâm Thân
  "9-9": "Kim",  // Quý Dậu

  // Sơn Đầu Hỏa (Mountain Top Fire)
  "0-10": "Hỏa",  // Giáp Tuất
  "1-11": "Hỏa",  // Ất Hợi

  // Giản Hạ Thủy (Stream Water)
  "2-0": "Thủy",  // Bính Tý
  "3-1": "Thủy",  // Đinh Sửu

  // Thành Đầu Thổ (City Wall Earth)
  "4-2": "Thổ",  // Mậu Dần
  "5-3": "Thổ",  // Kỷ Mão

  // Bạch Lạp Kim (White Wax Metal)
  "6-4": "Kim",  // Canh Thìn
  "7-5": "Kim",  // Tân Tỵ

  // Dương Liễu Mộc (Willow Wood)
  "8-6": "Mộc",  // Nhâm Ngọ
  "9-7": "Mộc",  // Quý Mùi

  // Tuyền Trung Thủy (Well Water)
  "0-8": "Thủy",  // Giáp Thân
  "1-9": "Thủy",  // Ất Dậu

  // Ốc Thượng Thổ (Rooftop Earth)
  "2-10": "Thổ",  // Bính Tuất
  "3-11": "Thổ",  // Đinh Hợi

  // Tướng Hỏa / Hích Lịch Hỏa (Thunderbolt Fire)
  "4-0": "Hỏa",  // Mậu Tý
  "5-1": "Hỏa",  // Kỷ Sửu

  // Tùng Bách Mộc (Pine Wood)
  "6-2": "Mộc",  // Canh Dần
  "7-3": "Mộc",  // Tân Mão

  // Trường Lưu Thủy (Long Flow Water)
  "8-4": "Thủy",  // Nhâm Thìn
  "9-5": "Thủy",  // Quý Tỵ

  // Sa Trung Kim (Sand Gold)
  "0-6": "Kim",  // Giáp Ngọ
  "1-7": "Kim",  // Ất Mùi

  // Sơn Hạ Hỏa (Below Mountain Fire)
  "2-8": "Hỏa",  // Bính Thân
  "3-9": "Hỏa",  // Đinh Dậu

  // Bình Địa Mộc (Flat Land Wood)
  "4-10": "Mộc",  // Mậu Tuất
  "5-11": "Mộc",  // Kỷ Hợi

  // Bích Thượng Thổ (Wall Earth)
  "6-0": "Thổ",  // Canh Tý
  "7-1": "Thổ",  // Tân Sửu

  // Kim Bạch Kim (Gold Foil Metal)
  "8-2": "Kim",  // Nhâm Dần
  "9-3": "Kim",  // Quý Mão

  // Phú Đăng Hỏa (Lamp Fire)
  "0-4": "Hỏa",  // Giáp Thìn
  "1-5": "Hỏa",  // Ất Tỵ

  // Thiên Hà Thủy (Heavenly River Water)
  "2-6": "Thủy",  // Bính Ngọ
  "3-7": "Thủy",  // Đinh Mùi

  // Đại Trạch Thổ (Great Desert Earth)
  "4-8": "Thổ",  // Mậu Thân
  "5-9": "Thổ",  // Kỷ Dậu

  // Thoa Xuyến Kim (Bracelet Metal)
  "6-10": "Kim",  // Canh Tuất
  "7-11": "Kim",  // Tân Hợi

  // Tang Đố Mộc (Mulberry Wood)
  "8-0": "Mộc",  // Nhâm Tý
  "9-1": "Mộc",  // Quý Sửu

  // Đại Khê Thủy (Great Stream Water)
  "0-2": "Thủy",  // Giáp Dần
  "1-3": "Thủy",  // Ất Mão

  // Sa Trung Thổ (Sand Earth)
  "2-4": "Thổ",  // Bính Thìn
  "3-5": "Thổ",  // Đinh Tỵ

  // Thiên Thượng Hỏa (Heavenly Fire)
  "4-6": "Hỏa",  // Mậu Ngọ
  "5-7": "Hỏa",  // Kỷ Mùi

  // Thạch Lựu Mộc (Pomegranate Wood)
  "6-8": "Mộc",  // Canh Thân
  "7-9": "Mộc",  // Tân Dậu

  // Đại Hải Thủy (Ocean Water)
  "8-10": "Thủy",  // Nhâm Tuất
  "9-11": "Thủy",  // Quý Hợi
}

function getNguHanhMenh(yearCanIndex, yearChiIndex) {
  return NAP_AM[`${yearCanIndex}-${yearChiIndex}`]
}
```

### Dương Thần and Kỵ Thần (Favorable / Unfavorable Elements)
```javascript
// Tương sinh: Kim→Thủy→Mộc→Hỏa→Thổ→Kim (cycle)
// getDuongThan = element that GENERATES the menh (tương sinh)
// getKyThan    = element that DESTROYS the menh (tương khắc)

const TUONG_SINH_NGUON = {  // what generates this element
  "Kim":  "Thổ",   // Thổ sinh Kim
  "Thủy": "Kim",   // Kim sinh Thủy
  "Mộc":  "Thủy",  // Thủy sinh Mộc
  "Hỏa":  "Mộc",   // Mộc sinh Hỏa
  "Thổ":  "Hỏa",   // Hỏa sinh Thổ
}

const TUONG_KHAC_BY = {  // what destroys this element
  "Kim":  "Hỏa",   // Hỏa khắc Kim
  "Thủy": "Thổ",   // Thổ khắc Thủy
  "Mộc":  "Kim",   // Kim khắc Mộc
  "Hỏa":  "Thủy",  // Thủy khắc Hỏa
  "Thổ":  "Mộc",   // Mộc khắc Thổ
}

function getDuongThan(menhElement) { return TUONG_SINH_NGUON[menhElement] }
function getKyThan(menhElement)    { return TUONG_KHAC_BY[menhElement] }
```

---

## 4. 12 TRỰC (DAY OFFICERS)

### Definition
The Trực of a day is determined by aligning the day's Địa Chi against the lunar month's ruling Chi.

### Lunar Month → Ruling Chi
```javascript
// Lunar month number → Chi index (0=Tý...11=Hợi)
const MONTH_CHI = {
  1: 2,   // Tháng Giêng → Dần
  2: 3,   // Tháng Hai → Mão
  3: 4,   // Tháng Ba → Thìn
  4: 5,   // Tháng Tư → Tỵ
  5: 6,   // Tháng Năm → Ngọ
  6: 7,   // Tháng Sáu → Mùi
  7: 8,   // Tháng Bảy → Thân
  8: 9,   // Tháng Tám → Dậu
  9: 10,  // Tháng Chín → Tuất
  10: 11, // Tháng Mười → Hợi
  11: 0,  // Tháng Mười Một → Tý
  12: 1,  // Tháng Chạp → Sửu
}
```

### 12 Trực in Order (index 0–11)
```javascript
const TRUC = [
  { index: 0,  name: "Kiến", score: 1,  note: "Tốt cho việc khởi đầu" },
  { index: 1,  name: "Trừ", score: 1,  note: "Tốt cho tẩy uế, chữa bệnh" },
  { index: 2,  name: "Mãn", score: 2,  note: "Viên mãn, rất tốt" },
  { index: 3,  name: "Bình", score: 1,  note: "Bình ổn, tốt chung" },
  { index: 4,  name: "Định", score: 2,  note: "Định vị, rất tốt cho hôn nhân và ký kết" },
  { index: 5,  name: "Chấp", score: 0,  note: "Trung tính, dùng được cho việc nhỏ" },
  { index: 6,  name: "Phá", score: -2, note: "XẤU — Layer 1 loại bỏ" },
  { index: 7,  name: "Nguy", score: -2, note: "XẤU — Layer 1 loại bỏ" },
  { index: 8,  name: "Thành", score: 2,  note: "Thành tựu, rất tốt mọi việc" },
  { index: 9,  name: "Thu", score: 0,  note: "Thu nhận — trung tính" },
  { index: 10, name: "Khai", score: 2,  note: "Khai thông, rất tốt cho khai trương" },
  { index: 11, name: "Bế", score: -1, note: "Khép lại, kém" },
]
```

### getTruc() Function
```javascript
function getTruc(dayChiIndex, lunarMonthNumber) {
  const monthChiIndex = MONTH_CHI[lunarMonthNumber]
  const trucIndex = ((dayChiIndex - monthChiIndex) + 12) % 12
  return TRUC[trucIndex]
}
```

### Layer 1 Discard Rule for Trực
Discard any day where Trực is Phá (index 6) or Nguy (index 7).

---

## 5. HUNG NGÀY — ABSOLUTE BAD DAYS (Layer 1)

### 5.1 Nguyệt Kỵ (Universal Bad Days) — severity 3
Lunar days 5, 14, 23 of EVERY month. No exceptions, no intent override.

### 5.2 Tam Nương (Widow Days) — severity 2, critical for CUOI_HOI
Lunar days: **3, 7, 13, 18, 22, 27** of every month.
- Severity 2 for all intents
- Severity 3 specifically for CUOI_HOI (must add to dates_to_avoid, never recommend)

### 5.3 Dương Công Kỵ Nhật (13 Most Inauspicious Days/Year) — severity 3
```javascript
const DUONG_CONG_KY = [
  { month: 1,  day: 13 },
  { month: 2,  day: 11 },
  { month: 3,  day: 9  },
  { month: 4,  day: 7  },
  { month: 5,  day: 5  },
  { month: 6,  day: 3  },
  { month: 7,  day: 1  },
  { month: 7,  day: 29 },
  { month: 8,  day: 27 },
  { month: 9,  day: 25 },
  { month: 10, day: 23 },
  { month: 11, day: 21 },
  { month: 12, day: 19 },
]
```

### 5.4 Tháng Cô Hồn (Ghost Month) — CUOI_HOI specific
Lunar month 7 (entire month). No wedding dates during this month.
If intent = CUOI_HOI and lunar month = 7 → move day to dates_to_avoid with severity 3.

### 5.5 Layer 1 Filter Pseudocode
```javascript
function filterLayer1(dateRange, intent) {
  return dateRange.filter(date => {
    const lunar = toLunar(date)
    const dayCC = getCanChiDay(date)
    const truc  = getTruc(dayCC.chiIndex, lunar.month)

    // Rule 1: Nguyệt Kỵ
    if ([5, 14, 23].includes(lunar.day)) return false

    // Rule 2: Tam Nương (severity 3 for CUOI_HOI, severity 2 otherwise)
    if ([3, 7, 13, 18, 22, 27].includes(lunar.day)) {
      if (intent === 'CUOI_HOI') return false
      // for other intents: still discard if severity >= 2
      return false
    }

    // Rule 3: Dương Công Kỵ Nhật
    const isDuongCong = DUONG_CONG_KY.some(
      r => r.month === lunar.month && r.day === lunar.day
    )
    if (isDuongCong) return false

    // Rule 4: Hung Trực
    if (truc.score <= -2) return false  // Phá, Nguy

    // Rule 5: Tháng Cô Hồn (Ghost Month)
    if (intent === 'CUOI_HOI' && lunar.month === 7) return false

    return true
  })
}
```

---

## 6. SAO NGÀY — DAY STARS (Layer 1 + Layer 3)

### 6.1 Thiên Đức (Heavenly Virtue Star)
A Cat Tinh. Day has Thiên Đức if the day's CAN matches the month's Thiên Đức Can:
```javascript
const THIEN_DUC_CAN = {
  1: 7,   // Month 1: Tân (index 7)
  2: 8,   // Month 2: Nhâm (index 8)
  3: 5,   // Month 3: Kỷ (index 5) — NOTE: Kỷ Chi for month 3 = Tuất, but Thiên Đức = Nhâm(8) or Đinh(3)
  // SME: Please verify the full table below before seeding.
  // Provisional table (needs SME sign-off):
  // Month: 1=Đinh(3), 2=Thân→not a can..
}
```
**⚠️ SME ACTION: Thiên Đức and Nguyệt Đức rules have multiple interpretations across schools.**
**Provide the exact Can list for months 1–12. Until confirmed, skip these stars in scoring.**

### 6.2 Stars Computable from Can Chi (implement these first)

#### Nhật Mã (Day Horse Star) — Cat Tinh for XUAT_HANH
```javascript
// Day has Nhật Mã if day's Chi matches this lookup by year's Chi:
const NHAT_MA = { 0:"Dần",2:"Thân",4:"Tỵ",6:"Hợi",8:"Thân",10:"Dần",1:"Hợi",3:"Tỵ",5:"Dần",7:"Thân",9:"Hợi",11:"Tỵ" }
// Key = year chi index, Value = day chi name that triggers star
```

#### Lục Hợp (Six Harmonies) — Cat Tinh, general auspicious
```javascript
// Day's chi harmonizes with year's chi:
const LUC_HOP_PAIRS = { 0:1, 1:0, 2:11, 11:2, 3:10, 10:3, 4:9, 9:4, 5:8, 8:5, 6:7, 7:6 }
// If LUC_HOP_PAIRS[yearChiIndex] === dayChiIndex → day has Lục Hợp
```

### 6.3 Absolute Hung Tinh (Layer 1 discard regardless of intent)
**SME must provide the algorithm to compute these. Until confirmed, use hung_ngay DB table only.**
- Thiên Hỏa (Heavenly Fire)
- Hoàng Sa
- Thiên Cương

---

## 7. GETCANCHI YEAR — for birth chart

```javascript
function getCanChiYear(year) {
  // Year 1900 = Canh Tý → canIndex=6, chiIndex=0
  // Can: (year - 1900 + 6) mod 10... but safer to use:
  const canIndex = ((year - 4) % 10 + 10) % 10
  const chiIndex = ((year - 4) % 12 + 12) % 12
  return { canIndex, chiIndex, can: CAN[canIndex], chi: CHI[chiIndex] }
}

// Verify: getCanChiYear(1900) → can=6(Canh), chi=0(Tý) → Canh Tý ✓
// Verify: getCanChiYear(1990) → (1990-4)%10=6→Canh, (1990-4)%12=6→Ngọ → Canh Ngọ ✓
// Verify: getCanChiYear(2024) → (2024-4)%10=0→Giáp, (2024-4)%12=4→Thìn → Giáp Thìn ✓
```

---

## 8. FULL computeBatTu() FLOW

```javascript
function computeBatTu(birthDate, birthTime = null) {
  const [y, m, d] = birthDate.split('-').map(Number)

  const yearCC  = getCanChiYear(y)
  const dayCC   = getCanChiDay(birthDate)
  // monthCC and hourCC: complex — implement after year+day are verified
  // For Phase 1, only yearCC is required for Layer 2 Xung/Khac check

  const nguHanhMenh = getNguHanhMenh(yearCC.canIndex, yearCC.chiIndex)
  const duongThan   = getDuongThan(nguHanhMenh)
  const kyThan      = getKyThan(nguHanhMenh)

  return {
    yearPillar: yearCC,
    dayPillar: dayCC,
    nguHanhMenh,
    duongThan,
    kyThan,
  }
}
```

---

## 9. LAYER 2 — filterLayer2() Full Logic

```javascript
function filterLayer2(candidates, chart) {
  const safeDays     = []
  const datesToAvoid = []

  for (const day of candidates) {
    const dayCC     = getCanChiDay(day.date)
    const yearChi   = chart.yearPillar.chiIndex
    const dayChi    = dayCC.chiIndex
    const yearCan   = chart.yearPillar.canIndex
    const dayCan    = dayCC.canIndex
    const dayHanh   = getNguHanhOfDay(dayCC)   // see below

    // Check 1: Địa Chi Tương Xung — severity 3 (hard reject)
    if (Math.abs(dayChi - yearChi) === 6) {
      datesToAvoid.push({ date: day.date, severity: 3,
        reason_vi: `Ngày ${CHI[dayChi]} Xung với tuổi ${CHI[yearChi]} của chủ nhân` })
      continue
    }

    // Check 2: Thiên Can Tương Khắc — severity 2 (reject)
    if (CAN_KHAC_MAP[dayCan] === yearCan) {
      datesToAvoid.push({ date: day.date, severity: 2,
        reason_vi: `Thiên Can ngày Khắc với Can năm sinh` })
      continue
    }

    // Check 3: Kỵ Thần element — severity 2 (reject)
    if (dayHanh === chart.kyThan) {
      datesToAvoid.push({ date: day.date, severity: 2,
        reason_vi: `Ngũ hành ngày Khắc với mệnh chủ nhân (${chart.nguHanhMenh})` })
      continue
    }

    safeDays.push({ ...day, dayCC, dayHanh })
  }

  return { safeDays, datesToAvoid }
}

// Can Khac Map: dayCan khắc yearCan (attacker → target)
const CAN_KHAC_MAP = { 0:4, 1:5, 2:6, 3:7, 4:8, 5:9, 6:0, 7:1, 8:2, 9:3 }
// 0(Giáp)→4(Mậu), 1(Ất)→5(Kỷ), ... etc.

function getNguHanhOfDay(dayCC) {
  // Use CAN's element (dominant for daily calculation)
  const CAN_HANH = ["Mộc","Mộc","Hỏa","Hỏa","Thổ","Thổ","Kim","Kim","Thủy","Thủy"]
  return CAN_HANH[dayCC.canIndex]
}
```

---

## 10. LAYER 3 — Scoring Weights Reference

```javascript
const SCORE_WEIGHTS = {
  base:             50,   // every day that passes Layer 2 starts at 50
  truc_required:    15,   // bonus if truc is in intent's required list
  truc_base_factor: 10,   // truc.score (-2 to +2) × 10
  cat_tinh_normal:  5,    // per Cat Tinh star on the day
  cat_tinh_bonus:   10,   // if star is in intent's bonus_sao list
  hung_tinh_normal: -8,   // per Hung Tinh star
  hung_tinh_forbidden: -15, // if in intent's forbidden list (may also disqualify)
  duong_than_match: 12,   // day element matches user's Dương Thần
}

// Grade thresholds
const GRADE = score => score >= 80 ? 'A' : score >= 65 ? 'B' : score >= 50 ? 'C' : 'D'
```

---

## 11. SAFETY GUARD (Required — do not skip)

Before building the final response, add this check:

```javascript
function buildResponse(recommendedDates, datesToAvoid, chart) {
  // SAFETY: re-validate every recommended date
  const safeRecommended = recommendedDates.filter(r => {
    const dayChiIndex = getCanChiDay(r.date).chiIndex
    const yearChiIndex = chart.yearPillar.chiIndex
    const isXung = Math.abs(dayChiIndex - yearChiIndex) === 6
    if (isXung) {
      console.error(`SAFETY VIOLATION: Xung day ${r.date} slipped into recommended`)
      return false
    }
    const isSeverity3InAvoid = datesToAvoid.some(a => a.date === r.date && a.severity === 3)
    if (isSeverity3InAvoid) {
      console.error(`SAFETY VIOLATION: severity-3 date ${r.date} slipped into recommended`)
      return false
    }
    return true
  })
  return { recommended_dates: safeRecommended, dates_to_avoid: datesToAvoid }
}
```


---

## 12. SAO NGÀY — DAY STARS SYSTEM

> Source: Ngọc Hạp Thông Thư. Implemented in `src/calendar-service.js`.
> Input for all functions: `lunarMonth` (1-12), `dayCanIdx` (0-9), `dayChiIdx` (0-11).

### 12.1 Thiên Đức (Celestial Virtue) — Cát tinh mạnh nhất
Mỗi tháng âm lịch, một Can hoặc Chi nhất định mang sao Thiên Đức.
Tháng 1,3,4,6,7,9,10,12 → dùng Thiên Can.
Tháng 2,5,8,11 → dùng Địa Chi.

| Lunar Month | Thiên Đức | type | index |
|-------------|-----------|------|-------|
| 1  | Đinh | can | 3 |
| 2  | Thân | chi | 8 |
| 3  | Nhâm | can | 8 |
| 4  | Tân  | can | 7 |
| 5  | Hợi  | chi | 11 |
| 6  | Giáp | can | 0 |
| 7  | Quý  | can | 9 |
| 8  | Dần  | chi | 2 |
| 9  | Bính | can | 2 |
| 10 | Ất   | can | 1 |
| 11 | Tỵ   | chi | 5 |
| 12 | Canh | can | 6 |

```javascript
// [{ type:'can'|'chi', idx:number }] — index = lunarMonth - 1
const THIEN_DUC = [
  {type:'can',idx:3},{type:'chi',idx:8},{type:'can',idx:8},{type:'can',idx:7},
  {type:'chi',idx:11},{type:'can',idx:0},{type:'can',idx:9},{type:'chi',idx:2},
  {type:'can',idx:2},{type:'can',idx:1},{type:'chi',idx:5},{type:'can',idx:6}
];
function hasThienDuc(lm, dayCanIdx, dayChiIdx) {
  const td = THIEN_DUC[lm-1];
  return td.type==='can' ? dayCanIdx===td.idx : dayChiIdx===td.idx;
}
```

### 12.2 Thiên Đức Hợp
Hợp của Thiên Đức. Tháng 2, 5, 8, 11 (tứ trọng) **không có** Thiên Đức Hợp theo sách cổ.

| Month | Thiên Đức Hợp | type | canIdx |
|-------|--------------|------|--------|
| 1  | Nhâm (hợp Đinh) | can | 8 |
| 2  | (không có)      | —   | — |
| 3  | Đinh (hợp Nhâm) | can | 3 |
| 4  | Bính (hợp Tân)  | can | 2 |
| 5  | (không có)      | —   | — |
| 6  | Kỷ   (hợp Giáp) | can | 5 |
| 7  | Mậu  (hợp Quý)  | can | 4 |
| 8  | (không có)      | —   | — |
| 9  | Tân  (hợp Bính) | can | 7 |
| 10 | Canh (hợp Ất)   | can | 6 |
| 11 | (không có)      | —   | — |
| 12 | Ất   (hợp Canh) | can | 1 |

```javascript
// null = tháng tứ trọng (không có hợp)
const THIEN_DUC_HOP = [8,null,3,2,null,5,4,null,7,6,null,1];
function hasThienDucHop(lm, dayCanIdx) {
  const tdh = THIEN_DUC_HOP[lm-1];
  return tdh !== null && dayCanIdx === tdh;
}
```

### 12.3 Nguyệt Đức (Monthly Virtue)
Dựa vào khí Tam Hợp của tháng — Can dương vượng của cục.

| Nhóm Tam Hợp | Tháng | Nguyệt Đức | canIdx |
|-------------|-------|-----------|--------|
| Dần/Ngọ/Tuất → Hỏa | 1, 5, 9  | Bính | 2 |
| Thân/Tý/Thìn → Thủy | 3, 7, 11 | Nhâm | 8 |
| Hợi/Mão/Mùi → Mộc  | 2, 6, 10 | Giáp | 0 |
| Tỵ/Dậu/Sửu → Kim   | 4, 8, 12 | Canh | 6 |

```javascript
const NGUYET_DUC_CAN = [2,0,8,6, 2,0,8,6, 2,0,8,6]; // index = lm-1
function hasNguyetDuc(lm, dayCanIdx) {
  return dayCanIdx === NGUYET_DUC_CAN[lm-1];
}
```

### 12.4 Nguyệt Đức Hợp

| Nhóm | Tháng | Nguyệt Đức Hợp | canIdx |
|------|-------|---------------|--------|
| Hỏa | 1, 5, 9  | Tân  (hợp Bính) | 7 |
| Thủy | 3, 7, 11 | Đinh (hợp Nhâm) | 3 |
| Mộc  | 2, 6, 10 | Kỷ   (hợp Giáp) | 5 |
| Kim  | 4, 8, 12 | Ất   (hợp Canh) | 1 |

```javascript
const NGUYET_DUC_HOP_CAN = [7,5,3,1, 7,5,3,1, 7,5,3,1]; // index = lm-1
function hasNguyetDucHop(lm, dayCanIdx) {
  return dayCanIdx === NGUYET_DUC_HOP_CAN[lm-1];
}
```

---

## 13. HUNG NGÀY — UNIVERSAL BAD DAYS (Layer 1)

### 13.1 Nguyệt Kỵ
Ngày âm lịch 5, 14, 23 của **mọi tháng**. Loại ở Layer 1.

### 13.2 Tam Nương
Ngày âm lịch 3, 7, 13, 18, 22, 27. Severity 3 cho CUOI_HOI.

### 13.3 Dương Công Kỵ Nhật (13 ngày trong năm)

| Tháng âm | Ngày âm |
|----------|---------|
| 1 | 13 |
| 2 | 11 |
| 3 | 9  |
| 4 | 7  |
| 5 | 5  |
| 6 | 3  |
| 7 | **1 và 29** |
| 8 | 27 |
| 9 | 25 |
| 10 | 23 |
| 11 | 21 |
| 12 | 19 |

```javascript
const DUONG_CONG_KY = {
  1:[13],2:[11],3:[9],4:[7],5:[5],6:[3],
  7:[1,29],8:[27],9:[25],10:[23],11:[21],12:[19]
};
```

---

## 14. GETDAYINFO() — Master Function

`getDayInfo(solarDateStr)` là entry point chính của `calendar-service.js`.
Trả về toàn bộ thông tin cần thiết cho Layer 1, 2, 3.

```javascript
// Input: '2026-03-11' (ISO date string)
// Output:
{
  date: '2026-03-11',
  // Can Chi
  dayCanIdx: 4,          // Mậu
  dayChiIdx: 2,          // Dần
  dayCanName: 'Mậu',
  dayChiName: 'Dần',
  // Lunar
  lunarDay: 12,
  lunarMonth: 2,
  lunarYear: 2026,
  isLeapMonth: false,
  // 12 Trực
  trucIdx: 3,            // Bình
  trucName: 'Bình',
  trucScore: 1,
  // Sao ngày
  hasThienDuc: false,
  hasThienDucHop: false,
  hasNguyetDuc: true,
  hasNguyetDucHop: false,
  napAmHanh: 'Thổ',      // Nạp âm ngũ hành của ngày (Mậu Dần = Thành Đầu Thổ)
  // Layer 1 flags (pre-computed)
  isNguyetKy: false,
  isTamNuong: false,
  isDuongCongKy: false,
  isTrucPha: false,      // trucIdx === 6
  isTrucNguy: false,     // trucIdx === 7
  isLayer1Pass: true,    // true = không bị loại ở Layer 1
}
```

---

## 15. HOÀNG ĐẠO / HẮC ĐẠO — 12-Star Day Classification

> ⚠️ SME verify: formula and star order sourced from traditional lịch vạn niên.

### 15.1 The 12 Stars (fixed order, repeating cycle)

```javascript
const STARS_12 = [
  { idx: 0,  name: "Thanh Long",  type: "hoang_dao" },
  { idx: 1,  name: "Minh Đường",  type: "hoang_dao" },
  { idx: 2,  name: "Thiên Hình",  type: "hac_dao"   },
  { idx: 3,  name: "Chu Tước",    type: "hac_dao"   },
  { idx: 4,  name: "Kim Quỹ",     type: "hoang_dao" },
  { idx: 5,  name: "Thiên Đức",   type: "hoang_dao" },  // ★ khác sao Thiên Đức §12
  { idx: 6,  name: "Bạch Hổ",     type: "hac_dao"   },
  { idx: 7,  name: "Ngọc Đường",  type: "hoang_dao" },
  { idx: 8,  name: "Thiên Lao",   type: "hac_dao"   },
  { idx: 9,  name: "Huyền Vũ",    type: "hac_dao"   },
  { idx: 10, name: "Tư Mệnh",    type: "hoang_dao" },
  { idx: 11, name: "Câu Trận",   type: "hac_dao"   },
]
// 6 Hoàng Đạo: indices {0, 1, 4, 5, 7, 10}
// 6 Hắc Đạo:   indices {2, 3, 6, 8, 9, 11}
```

### 15.2 Starting Position per Lunar Month

Thanh Long (star index 0) sits at this Địa Chi for each lunar month:

| Lunar Month | Start Chi | Chi Index |
|-------------|-----------|-----------|
| 1, 7   | Tý    | 0  |
| 2, 8   | Dần   | 2  |
| 3, 9   | Thìn  | 4  |
| 4, 10  | Ngọ   | 6  |
| 5, 11  | Thân  | 8  |
| 6, 12  | Tuất  | 10 |

Formula: `startChi = ((lunarMonth - 1) % 6) * 2`

### 15.3 Calculation

```javascript
function getDayStar(lunarMonth, dayChiIdx) {
  const startChi = ((lunarMonth - 1) % 6) * 2
  const starIdx = ((dayChiIdx - startChi) % 12 + 12) % 12
  return STARS_12[starIdx]
}

function isHoangDao(lunarMonth, dayChiIdx) {
  const starIdx = ((dayChiIdx - ((lunarMonth - 1) % 6) * 2) % 12 + 12) % 12
  return [0, 1, 4, 5, 7, 10].includes(starIdx)
}
```

### 15.4 Verified Test Vectors
```
Lunar Month 1, Chi Tý(0)   → star 0 → Thanh Long  (Hoàng Đạo) ✓
Lunar Month 1, Chi Ngọ(6)  → star 6 → Bạch Hổ    (Hắc Đạo)   ✓
Lunar Month 3, Chi Thìn(4) → star 0 → Thanh Long  (Hoàng Đạo) ✓
Lunar Month 4, Chi Ngọ(6)  → star 0 → Thanh Long  (Hoàng Đạo) ✓
```

---

## 16. GIỜ HOÀNG ĐẠO — Good Hours per Day

> ⚠️ SME verify: hour sets sourced from traditional lịch vạn niên.

### 16.1 12 Giờ (Double-hour blocks)

| Giờ | Chi Index | Time Range |
|-----|-----------|------------|
| Tý  | 0  | 23:00 – 01:00 |
| Sửu | 1  | 01:00 – 03:00 |
| Dần | 2  | 03:00 – 05:00 |
| Mão | 3  | 05:00 – 07:00 |
| Thìn| 4  | 07:00 – 09:00 |
| Tỵ  | 5  | 09:00 – 11:00 |
| Ngọ | 6  | 11:00 – 13:00 |
| Mùi | 7  | 13:00 – 15:00 |
| Thân| 8  | 15:00 – 17:00 |
| Dậu | 9  | 17:00 – 19:00 |
| Tuất| 10 | 19:00 – 21:00 |
| Hợi | 11 | 21:00 – 23:00 |

### 16.2 Good Hours by Day Chi

| Day Chi (index) | Good Hour Chi Indices |
|----------------|----------------------|
| Even (Tý=0, Dần=2, Thìn=4, Ngọ=6, Thân=8, Tuất=10) | {0, 1, 4, 5, 7, 10} — Tý, Sửu, Thìn, Tỵ, Mùi, Tuất |
| Odd (Sửu=1, Mão=3, Tỵ=5, Mùi=7, Dậu=9, Hợi=11) | {2, 3, 5, 6, 8, 11} — Dần, Mão, Tỵ, Ngọ, Thân, Hợi |

Formula: `dayChiIdx % 2 == 0 → GOOD_EVEN; dayChiIdx % 2 == 1 → GOOD_ODD`

Each day always has exactly 6 good hours (Hoàng Đạo) and 6 bad hours (Hắc Đạo).

```javascript
const GOOD_HOURS_EVEN = new Set([0, 1, 4, 5, 7, 10])
const GOOD_HOURS_ODD  = new Set([2, 3, 5, 6, 8, 11])

function getGioHoangDao(dayChiIdx) {
  return dayChiIdx % 2 === 0 ? GOOD_HOURS_EVEN : GOOD_HOURS_ODD
}
```

---

## 17. ĐẠI VẬN (大运) — 10-Year Luck Cycles

Used when Tứ Trụ + gender are known (`engine/dai_van.py`).

### 17.1 Hướng đại vận (顺 / 逆)

Theo **Can năm** (Dương = Giáp Bính Mậu Canh Nhâm) và **giới tính**:

- **Nam (1):** Can năm Dương → thuận (+1); Can năm Âm → nghịch (−1).
- **Nữ (−1):** Ngược lại nam.

### 17.2 Trụ bắt đầu

Mỗi bước đại vận: từ **Nguyệt trụ** (月柱), cùng bước nhịp **Thiên Can** và **Địa Chi** theo hướng (một bước trong chuỗi 60 Giáp Tý).

### 17.3 Tuổi khởi vận (起运)

- **Thuận:** đếm **ngày dương lịch** từ ngày sinh đến **ngày bắt đầu tiết 节 kế tiếp** (sau ngày sinh, không tính trùng ngày nếu sinh đúng ngày đổi 节).
- **Nghịch:** đếm ngày từ **ngày bắt đầu tiết 节 liền trước** đến ngày sinh.

**Chỉ dùng mười hai 节** (ranh giới tháng tiết: Lập Xuân, Kinh Trập, Thanh Minh, …). **Không** dùng mười hai 气 (Vũ Thủy, Xuân Phân, Cốc Vũ, …).

Công thức gần đúng phổ biến: `ba ngày ≈ một năm khởi vận` → `tuổi_khởi_vận = max(1, round(số_ngày / 3))`.

Xác định 节 trên lịch: dùng kinh độ Mặt Trời (24 tiết, mỗi 15°). Với bucket `b = floor((λ mod 360°) / 15°) mod 24`, các **节** ứng với bucket **lẻ** (1, 3, …, 21, 23) trong ánh xạ cùng `bazi_solar.solar_term_bucket`.

### 17.4 Chu kỳ hiện tại

So tuổi đã tròn (năm − năm sinh, trừ 1 nếu chưa tới sinh nhật trong năm dương) với khoảng `[start_age, end_age]` của từng đại vận (`start_age` của vận 1 = tuổi khởi vận; mỗi vận 10 năm).

**Ghi chú:** Hiện tại tuổi khởi vận chỉ theo **ngày** sinh (không tinh chỉnh theo **giờ** sinh); một số phái lịch tính theo giờ — có thể mở rộng sau.

## 18. Phong thủy API và Phi Tinh (GET /v1/phong-thuy, version 2)

**Dụng Thần / Kỵ Thần / hướng–màu–số:** Khi không có `birth_time`, lấy Dương Thần / Kỵ Thần từ **Nạp Âm năm sinh** (`get_menh_nap_am_from_date` theo ngày sinh, ranh giới Lập Xuân). Khi có `birth_time`, dùng `find_dung_than` trên Tứ Trụ. Gợi ý vật phẩm theo mục đích đọc từ `docs/seed/phong-thuy-purposes.json`; hóa giải cặp đôi (Nạp Âm tương khắc trực tiếp) từ `phong-thuy-couple-remedies.json`.

**Phi Tinh (Cửu cung lưu niên):** Tính theo **năm dương lịch** tham số `year`. **Nhập trung:** mặc định neo năm 2024 = sao 3, mỗi năm giảm 1 (mod 9, 0 → 9); có thể ghi đè từng năm trong `docs/seed/phi-tinh-year-center.json` (chỉ số nhập trung 1–9). **Thuận / nghịch phi:** theo **can năm Gregorian** `(year - 4) % 10` chẵn → Dương can (thuận phi), lẻ → Âm can (nghịch phi) — **không** dùng tiết Lập Xuân hay năm âm lịch. Do đó có thể lệch một số bảng sách hoặc phần mềm khác.

**Hướng tốt / xấu năm (`huong_tot_nam_nay` / `huong_xau_nam_nay`):** Phân loại theo trường `nature` của từng sao trong `phi-tinh-stars.json` — **không** lọc theo Dụng Thần cá nhân. Ghi chú giải thích thêm nằm trong `phi_tinh_note_vi` của response.

**Override nhập trung:** Nếu JSON override khác với công thức mà vẫn giữ cùng quy ước thuận/nghịch theo can dương lịch, có thể xảy ra tổ hợp không trùng mọi tài liệu truyền thống — client nên đọc `docs/seed/phi-tinh-year-center.json` (`_comment`) và phần mô tả API.
