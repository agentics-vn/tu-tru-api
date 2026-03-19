/**
 * calendar-service.js
 *
 * Layer 1 calendar engine for the Bát Tự Date Selection API.
 * Implements all universal day-quality calculations:
 *   - Solar → Lunar conversion (via amlich)
 *   - Can Chi Day / Year
 *   - 12 Trực
 *   - Sao Ngày: Thiên Đức, Thiên Đức Hợp, Nguyệt Đức, Nguyệt Đức Hợp
 *   - Hung Ngày: Nguyệt Kỵ, Tam Nương, Dương Công Kỵ Nhật
 *
 * Dependency: npm install amlich
 * Source of truth: docs/algorithm.md §2, §4, §12, §13, §14
 *
 * All results are plain JSON — no class instances, no side effects.
 * Safe to cache at Redis with key pattern "day:{YYYY-MM-DD}".
 */

'use strict';

const amlich = require('amlich');

// ─────────────────────────────────────────────────────────────────────────────
// 1. LOOKUP TABLES
// ─────────────────────────────────────────────────────────────────────────────

const CAN_NAMES  = ['Giáp','Ất','Bính','Đinh','Mậu','Kỷ','Canh','Tân','Nhâm','Quý'];
const CHI_NAMES  = ['Tý','Sửu','Dần','Mão','Thìn','Tỵ','Ngọ','Mùi','Thân','Dậu','Tuất','Hợi'];
const CAN_HANH   = ['Mộc','Mộc','Hỏa','Hỏa','Thổ','Thổ','Kim','Kim','Thủy','Thủy'];
const CHI_HANH   = ['Thủy','Thổ','Mộc','Mộc','Thổ','Hỏa','Hỏa','Thổ','Kim','Kim','Thổ','Thủy'];

// 30 Nạp Âm pairs — index = canChiPairIndex (0..29)
// pairIndex = floor((canIdx * 6 + floor(chiIdx/2)) % 30)  — see getMenhNapAm()
const NAP_AM_HANH = [
  'Kim',  // 0  Giáp Tý / Ất Sửu      Hải Trung Kim
  'Hỏa',  // 1  Bính Dần / Đinh Mão   Lò Trung Hỏa
  'Mộc',  // 2  Mậu Thìn / Kỷ Tỵ      Đại Lâm Mộc
  'Thổ',  // 3  Canh Ngọ / Tân Mùi    Lộ Bàng Thổ
  'Kim',  // 4  Nhâm Thân / Quý Dậu   Kiếm Phong Kim
  'Hỏa',  // 5  Giáp Tuất / Ất Hợi    Sơn Đầu Hỏa
  'Thủy', // 6  Bính Tý / Đinh Sửu    Giản Hạ Thủy
  'Thổ',  // 7  Mậu Dần / Kỷ Mão      Thành Đầu Thổ
  'Kim',  // 8  Canh Thìn / Tân Tỵ    Bạch Lạp Kim
  'Mộc',  // 9  Nhâm Ngọ / Quý Mùi    Dương Liễu Mộc
  'Thủy', // 10 Giáp Thân / Ất Dậu    Tuyền Trung Thủy
  'Thổ',  // 11 Bính Tuất / Đinh Hợi  Ốc Thượng Thổ
  'Hỏa',  // 12 Mậu Tý / Kỷ Sửu       Tích Lịch Hỏa
  'Mộc',  // 13 Canh Dần / Tân Mão    Tùng Bách Mộc
  'Thủy', // 14 Nhâm Thìn / Quý Tỵ   Trường Lưu Thủy
  'Kim',  // 15 Giáp Ngọ / Ất Mùi     Sa Trung Kim
  'Hỏa',  // 16 Bính Thân / Đinh Dậu  Sơn Hạ Hỏa
  'Mộc',  // 17 Mậu Tuất / Kỷ Hợi     Bình Địa Mộc
  'Thổ',  // 18 Canh Tý / Tân Sửu     Bích Thượng Thổ
  'Kim',  // 19 Nhâm Dần / Quý Mão    Kim Bạch Kim
  'Hỏa',  // 20 Giáp Thìn / Ất Tỵ    Phú Đăng Hỏa
  'Thủy', // 21 Bính Ngọ / Đinh Mùi   Thiên Hà Thủy
  'Thổ',  // 22 Mậu Thân / Kỷ Dậu     Đại Dịch Thổ
  'Kim',  // 23 Canh Tuất / Tân Hợi   Thoa Xuyến Kim
  'Mộc',  // 24 Nhâm Tý / Quý Sửu     Tang Đố Mộc
  'Thủy', // 25 Giáp Dần / Ất Mão     Đại Khê Thủy
  'Thổ',  // 26 Bính Thìn / Đinh Tỵ   Sa Trung Thổ
  'Hỏa',  // 27 Mậu Ngọ / Kỷ Mùi      Thiên Thượng Hỏa
  'Mộc',  // 28 Canh Thân / Tân Dậu   Thạch Lựu Mộc
  'Thủy', // 29 Nhâm Tuất / Quý Hợi   Đại Hải Thủy
];

const NAP_AM_NAMES = [
  'Hải Trung Kim','Lò Trung Hỏa','Đại Lâm Mộc','Lộ Bàng Thổ','Kiếm Phong Kim','Sơn Đầu Hỏa',
  'Giản Hạ Thủy','Thành Đầu Thổ','Bạch Lạp Kim','Dương Liễu Mộc','Tuyền Trung Thủy','Ốc Thượng Thổ',
  'Tích Lịch Hỏa','Tùng Bách Mộc','Trường Lưu Thủy','Sa Trung Kim','Sơn Hạ Hỏa','Bình Địa Mộc',
  'Bích Thượng Thổ','Kim Bạch Kim','Phú Đăng Hỏa','Thiên Hà Thủy','Đại Dịch Thổ','Thoa Xuyến Kim',
  'Tang Đố Mộc','Đại Khê Thủy','Sa Trung Thổ','Thiên Thượng Hỏa','Thạch Lựu Mộc','Đại Hải Thủy',
];

// 12 Trực
const TRUC_NAMES  = ['Kiến','Trừ','Mãn','Bình','Định','Chấp','Phá','Nguy','Thành','Thu','Khai','Bế'];
const TRUC_SCORES = [1, 1, 2, 1, 2, 0, -2, -2, 2, 0, 2, -1];
// Month Chi anchors: lunarMonth 1→Dần(2), 2→Mão(3) ... 11→Tý(0), 12→Sửu(1)
const MONTH_CHI_IDX = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]; // index = lm-1

// Thiên Đức: type 'can'|'chi', idx = can/chi index
const THIEN_DUC = [
  {type:'can',idx:3},  // month 1:  Đinh
  {type:'chi',idx:8},  // month 2:  Thân
  {type:'can',idx:8},  // month 3:  Nhâm
  {type:'can',idx:7},  // month 4:  Tân
  {type:'chi',idx:11}, // month 5:  Hợi
  {type:'can',idx:0},  // month 6:  Giáp
  {type:'can',idx:9},  // month 7:  Quý
  {type:'chi',idx:2},  // month 8:  Dần
  {type:'can',idx:2},  // month 9:  Bính
  {type:'can',idx:1},  // month 10: Ất
  {type:'chi',idx:5},  // month 11: Tỵ
  {type:'can',idx:6},  // month 12: Canh
];

// Thiên Đức Hợp: can index, null = tháng tứ trọng (không có)
const THIEN_DUC_HOP = [8, null, 3, 2, null, 5, 4, null, 7, 6, null, 1]; // index = lm-1

// Nguyệt Đức: Can index of Nguyệt Đức per month
const NGUYET_DUC_CAN     = [2, 0, 8, 6,  2, 0, 8, 6,  2, 0, 8, 6]; // index = lm-1
// Nguyệt Đức Hợp: Can index
const NGUYET_DUC_HOP_CAN = [7, 5, 3, 1,  7, 5, 3, 1,  7, 5, 3, 1]; // index = lm-1

// Dương Công Kỵ Nhật — 13 dates total
const DUONG_CONG_KY = {
  1:[13], 2:[11], 3:[9],  4:[7],
  5:[5],  6:[3],  7:[8,29], 8:[27],
  9:[25], 10:[23], 11:[21], 12:[19],
};

// Tam Nương days
const TAM_NUONG_DAYS = new Set([3, 7, 13, 18, 22, 27]);

// Dương Thần / Kỵ Thần lookup by Nạp Âm Mệnh
const DUONG_THAN = { Kim:'Thổ', Mộc:'Thủy', Thủy:'Kim', Hỏa:'Mộc', Thổ:'Hỏa' };
const KY_THAN    = { Kim:'Hỏa', Mộc:'Kim',  Thủy:'Thổ', Hỏa:'Thủy', Thổ:'Mộc' };

// ─────────────────────────────────────────────────────────────────────────────
// 2. CORE PRIMITIVES
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Julian Day Number (integer) from Gregorian date.
 * Used for Can Chi day calculation only.
 */
function getJDN(y, m, d) {
  const a  = Math.floor((14 - m) / 12);
  const yr = y + 4800 - a;
  const mo = m + 12 * a - 3;
  return d
    + Math.floor((153 * mo + 2) / 5)
    + 365 * yr
    + Math.floor(yr / 4)
    - Math.floor(yr / 100)
    + Math.floor(yr / 400)
    - 32045;
}

// Anchor: 1900-01-31 = Giáp Tý
const ANCHOR_JDN = 2415051;

/**
 * Can Chi index for a solar date.
 * @returns {{ canIdx, chiIdx, canName, chiName }}
 */
function getCanChiDay(year, month, day) {
  const jdn    = getJDN(year, month, day);
  const offset = jdn - ANCHOR_JDN;
  const canIdx = ((offset % 10) + 10) % 10;
  const chiIdx = ((offset % 12) + 12) % 12;
  return {
    canIdx,
    chiIdx,
    canName : CAN_NAMES[canIdx],
    chiName : CHI_NAMES[chiIdx],
    canHanh : CAN_HANH[canIdx],
    chiHanh : CHI_HANH[chiIdx],
  };
}

/**
 * Can Chi index for a solar year.
 * @returns {{ canIdx, chiIdx, canName, chiName }}
 */
function getCanChiYear(solarYear) {
  const canIdx = ((solarYear - 4) % 10 + 10) % 10;
  const chiIdx = ((solarYear - 4) % 12 + 12) % 12;
  return {
    canIdx,
    chiIdx,
    canName : CAN_NAMES[canIdx],
    chiName : CHI_NAMES[chiIdx],
  };
}

/**
 * Nạp Âm pair index (0-29) from year's Can Chi.
 * pairIndex corresponds to one of 30 NAP_AM pairs.
 *
 * Full cycle of 60 = 30 pairs × 2. Within each 60-year cycle,
 * each pair repeats exactly twice (once for each gender).
 * We collapse to 30 by floor(cyclePos / 2).
 */
function getNapAmPairIdx(canIdx, chiIdx) {
  // CRT: unique 60-cycle position where pos%10==canIdx AND pos%12==chiIdx
  // Verified: Giáp Tý→0, Ất Sửu→0, Bính Dần→1, Canh Ngọ→3,
  //           Ất Mão→25, Giáp Thìn→20, Bính Ngọ→21
  const cyclePos = (canIdx * 36 + chiIdx * 25) % 60;
  return Math.floor(cyclePos / 2);
}

/**
 * Nạp Âm mệnh (ngũ hành) for a birth year.
 * @param {number} birthYear - Solar year
 * @returns {{ hanh, name }} e.g. { hanh: 'Kim', name: 'Hải Trung Kim' }
 */
function getMenhNapAm(birthYear) {
  const { canIdx, chiIdx } = getCanChiYear(birthYear);
  const pairIdx = getNapAmPairIdx(canIdx, chiIdx);
  return {
    hanh : NAP_AM_HANH[pairIdx],
    name : NAP_AM_NAMES[pairIdx],
    duongThan : DUONG_THAN[NAP_AM_HANH[pairIdx]],
    kyThan    : KY_THAN[NAP_AM_HANH[pairIdx]],
  };
}

/**
 * Convert solar date string to lunar date.
 * @param {string} isoDate - 'YYYY-MM-DD'
 * @returns {{ lunarDay, lunarMonth, lunarYear, isLeapMonth }}
 */
function solarToLunar(isoDate) {
  const [y, m, d] = isoDate.split('-').map(Number);
  const [ld, lm, ly, leap] = amlich.convertSolar2Lunar(d, m, y, 7.0);
  return {
    lunarDay   : ld,
    lunarMonth : lm,
    lunarYear  : ly,
    isLeapMonth: leap === 1,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. 12 TRỰC
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Calculate Trực index (0-11) from day Chi and lunar month.
 * @param {number} dayChiIdx - 0-11
 * @param {number} lunarMonth - 1-12 (use main month, ignore leap)
 * @returns {number} 0-11
 */
function getTrucIdx(dayChiIdx, lunarMonth) {
  const monthChiIdx = MONTH_CHI_IDX[lunarMonth - 1];
  return ((dayChiIdx - monthChiIdx) % 12 + 12) % 12;
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. SAO NGÀY
// ─────────────────────────────────────────────────────────────────────────────

function checkThienDuc(lunarMonth, dayCanIdx, dayChiIdx) {
  const td = THIEN_DUC[lunarMonth - 1];
  return td.type === 'can' ? dayCanIdx === td.idx : dayChiIdx === td.idx;
}

function checkThienDucHop(lunarMonth, dayCanIdx) {
  const tdh = THIEN_DUC_HOP[lunarMonth - 1];
  return tdh !== null && dayCanIdx === tdh;
}

function checkNguyetDuc(lunarMonth, dayCanIdx) {
  return dayCanIdx === NGUYET_DUC_CAN[lunarMonth - 1];
}

function checkNguyetDucHop(lunarMonth, dayCanIdx) {
  return dayCanIdx === NGUYET_DUC_HOP_CAN[lunarMonth - 1];
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. HUNG NGÀY
// ─────────────────────────────────────────────────────────────────────────────

function isNguyetKy(lunarDay) {
  return lunarDay === 5 || lunarDay === 14 || lunarDay === 23;
}

function isTamNuong(lunarDay) {
  return TAM_NUONG_DAYS.has(lunarDay);
}

function isDuongCongKy(lunarMonth, lunarDay) {
  return (DUONG_CONG_KY[lunarMonth] || []).includes(lunarDay);
}

function isCohon(lunarMonth) {
  return lunarMonth === 7;
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. MASTER DAY INFO
// ─────────────────────────────────────────────────────────────────────────────

/**
 * getDayInfo — primary entry point.
 *
 * Returns all Layer-1 relevant data for a single solar date.
 * Output is a plain JSON object — safe to serialize to Redis.
 *
 * @param {string} isoDate - 'YYYY-MM-DD'
 * @returns {DayInfo}
 */
function getDayInfo(isoDate) {
  const [y, m, d] = isoDate.split('-').map(Number);

  // Lunar
  const lunar    = solarToLunar(isoDate);
  const lm       = lunar.lunarMonth;
  const ld       = lunar.lunarDay;

  // Can Chi Day
  const canChi   = getCanChiDay(y, m, d);
  const { canIdx, chiIdx } = canChi;
  const dayCanIdx = canIdx; // alias for return object clarity

  // Nạp Âm of the day (not the person — used for scoring element match)
  const dayPairIdx  = getNapAmPairIdx(canIdx, chiIdx);
  const dayNapAmHanh = NAP_AM_HANH[dayPairIdx];

  // 12 Trực
  const trucIdx   = getTrucIdx(chiIdx, lm);
  const trucScore = TRUC_SCORES[trucIdx];

  // Sao ngày
  const hasThienDuc    = checkThienDuc(lm, canIdx, chiIdx);
  const hasThienDucHop = checkThienDucHop(lm, canIdx);
  const hasNguyetDuc   = checkNguyetDuc(lm, canIdx);
  const hasNguyetDucHop= checkNguyetDucHop(lm, canIdx);

  // Hung ngày
  const _isNguyetKy   = isNguyetKy(ld);
  const _isTamNuong   = isTamNuong(ld);
  const _isDuongCongKy= isDuongCongKy(lm, ld);
  const isTrucPha     = trucIdx === 6;
  const isTrucNguy    = trucIdx === 7;

  // Layer 1 pass = none of the universal discard rules triggered
  const isLayer1Pass  = !_isNguyetKy
                      && !_isTamNuong
                      && !_isDuongCongKy
                      && !isTrucPha
                      && !isTrucNguy;

  return {
    date            : isoDate,
    // Solar
    solarDay        : d,
    solarMonth      : m,
    solarYear       : y,
    // Can Chi Day
    dayCanIdx,
    dayChiIdx       : chiIdx,
    dayCanName      : canChi.canName,
    dayChiName      : canChi.chiName,
    dayCanHanh      : canChi.canHanh,
    // Nạp Âm of day
    dayNapAmHanh,
    // Lunar
    lunarDay        : ld,
    lunarMonth      : lm,
    lunarYear       : lunar.lunarYear,
    isLeapMonth     : lunar.isLeapMonth,
    // 12 Trực
    trucIdx,
    trucName        : TRUC_NAMES[trucIdx],
    trucScore,
    // Sao ngày
    hasThienDuc,
    hasThienDucHop,
    hasNguyetDuc,
    hasNguyetDucHop,
    // Hung ngày flags
    isNguyetKy      : _isNguyetKy,
    isTamNuong      : _isTamNuong,
    isDuongCongKy   : _isDuongCongKy,
    isTrucPha,
    isTrucNguy,
    // Layer 1 summary
    isLayer1Pass,
    // Cohon (tháng 7) — checked against intent in controller, not here
    isCohon         : isCohon(lm),
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. MONTH INFO (for Redis cache warming)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * getMonthInfo — compute Layer 1 data for every day in a solar month.
 *
 * Cache key: "L1:{YYYY-MM}"  TTL: 30 days
 * Returns array of DayInfo objects, filtered to isLayer1Pass only if filterPassed=true.
 *
 * @param {number} year
 * @param {number} month  - 1-12
 * @param {boolean} [filterPassed=false] - if true, returns only days that pass Layer 1
 * @returns {DayInfo[]}
 */
function getMonthInfo(year, month, filterPassed = false) {
  const daysInMonth = new Date(year, month, 0).getDate(); // month is 1-indexed, trick: day 0 of next month
  const results = [];

  for (let d = 1; d <= daysInMonth; d++) {
    const mm    = String(month).padStart(2, '0');
    const dd    = String(d).padStart(2, '0');
    const isoDate = `${year}-${mm}-${dd}`;
    const info  = getDayInfo(isoDate);
    if (!filterPassed || info.isLayer1Pass) {
      results.push(info);
    }
  }

  return results;
}

// ─────────────────────────────────────────────────────────────────────────────
// 8. USER CHART HELPERS (used by Layer 2 in filter.js)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * getUserChart — derive personal chart from birth date.
 * Output is passed to Layer 2 filter.
 *
 * @param {string} birthDate - 'YYYY-MM-DD'
 * @returns {UserChart}
 */
function getUserChart(birthDate) {
  const [y] = birthDate.split('-').map(Number);
  const yearCanChi = getCanChiYear(y);
  const menh       = getMenhNapAm(y);

  return {
    birthYear        : y,
    yearCanIdx       : yearCanChi.canIdx,
    yearChiIdx       : yearCanChi.chiIdx,
    yearCanName      : yearCanChi.canName,
    yearChiName      : yearCanChi.chiName,
    menhHanh         : menh.hanh,
    menhName         : menh.name,
    duongThan        : menh.duongThan,
    kyThan           : menh.kyThan,
  };
}

/**
 * isXung — địa chi tương xung (severity 3).
 * @param {number} chiA
 * @param {number} chiB
 */
function isXung(chiA, chiB) {
  return Math.abs(chiA - chiB) === 6;
}

// Can Khắc map: dayCan khắc yearCan
// Giáp(0)→Mậu(4), Ất(1)→Kỷ(5), Bính(2)→Canh(6), Đinh(3)→Tân(7),
// Mậu(4)→Nhâm(8), Kỷ(5)→Quý(9), Canh(6)→Giáp(0), Tân(7)→Ất(1),
// Nhâm(8)→Bính(2), Quý(9)→Đinh(3)
const CAN_KHAC_MAP = { 0:4, 1:5, 2:6, 3:7, 4:8, 5:9, 6:0, 7:1, 8:2, 9:3 };

/**
 * isCanKhac — thiên can tương khắc (severity 2).
 * Returns true if dayCanIdx ATTACKS yearCanIdx.
 */
function isCanKhac(dayCanIdx, yearCanIdx) {
  return CAN_KHAC_MAP[dayCanIdx] === yearCanIdx;
}

// ─────────────────────────────────────────────────────────────────────────────
// 9. EXPORTS
// ─────────────────────────────────────────────────────────────────────────────

module.exports = {
  // Core
  getDayInfo,
  getMonthInfo,
  getUserChart,
  // Primitives (exported for testing)
  getJDN,
  getCanChiDay,
  getCanChiYear,
  getMenhNapAm,
  getNapAmPairIdx,
  solarToLunar,
  // Trực
  getTrucIdx,
  // Sao checks
  checkThienDuc,
  checkThienDucHop,
  checkNguyetDuc,
  checkNguyetDucHop,
  // Hung checks
  isNguyetKy,
  isTamNuong,
  isDuongCongKy,
  isCohon,
  // Layer 2 helpers
  isXung,
  isCanKhac,
  // Tables (exported for reference/testing)
  CAN_NAMES,
  CHI_NAMES,
  TRUC_NAMES,
  TRUC_SCORES,
  NAP_AM_HANH,
  NAP_AM_NAMES,
  DUONG_THAN,
  KY_THAN,
};
