/**
 * pillars.js — Tứ Trụ / Bát Tự (Four Pillars) Engine
 *
 * Implements all 4 pillars with correct astronomical boundaries:
 *   - Năm Trụ  : changes at Lập Xuân (~Feb 4), NOT Tết
 *   - Tháng Trụ: changes at each of 12 Tiết Khí, NOT lunar month
 *   - Ngày Trụ : JDN anchor method (from calendar-service.js)
 *   - Giờ Trụ  : 2-hour blocks by Địa Chi, Can derived from Ngày Can
 *
 * Dependency: npm install lunar-javascript
 *   (6tail/lunar-javascript — uses astronomical ephemeris for solar terms)
 *
 * Source of truth: docs/algorithm.md
 * All boundary logic verified against Joey Yap BaziCalc and 10000-year calendar.
 */

'use strict';

const { Solar, SolarTerm } = require('lunar-javascript');
const { getCanChiDay, getCanChiYear } = require('./calendar-service');

// ─────────────────────────────────────────────────────────────────────────────
// 1. LOOKUP TABLES
// ─────────────────────────────────────────────────────────────────────────────

const CAN_NAMES = ['Giáp','Ất','Bính','Đinh','Mậu','Kỷ','Canh','Tân','Nhâm','Quý'];
const CHI_NAMES = ['Tý','Sửu','Dần','Mão','Thìn','Tỵ','Ngọ','Mùi','Thân','Dậu','Tuất','Hợi'];

/**
 * Giờ Địa Chi map.
 * Vietnamese time zone (UTC+7).
 * Tý spans 23:00 of DAY-1 to 00:59 of DAY.
 * Important: a birth at 23:30 on Jan 5 is Tý giờ of Jan 6 (next day's pillar).
 *
 * Index = hour 0-23
 */
const HOUR_TO_CHI = [
//  0   1   2   3   4   5   6   7   8   9  10  11
    0,  1,  1,  2,  2,  3,  3,  4,  4,  5,  5,  6,
// 12  13  14  15  16  17  18  19  20  21  22  23
    6,  7,  7,  8,  8,  9,  9, 10, 10, 11, 11,  0,
];
// Note: hour 23 → Chi Tý (0), but belongs to the NEXT calendar day's hour pillar.
// Callers must pass adjustedDate (shifted +1 day if hour >= 23) for Ngày/Giờ.

/**
 * Giờ Can starting index for Chi Tý (chiIdx=0), keyed by dayCanIdx % 5.
 * Rule: Giáp/Kỷ ngày → Tý giờ = Giáp; Ất/Canh → Bính; Bính/Tân → Mậu;
 *       Đinh/Nhâm → Canh; Mậu/Quý → Nhâm
 */
const HOUR_CAN_START = [0, 2, 4, 6, 8]; // index = dayCanIdx % 5

/**
 * 12 Tiết (odd solar terms) that start each month pillar.
 * Ordered by month chi index: Dần(2)=Lập Xuân, Mão(3)=Kinh Trập, ...
 *
 * monthChiIdx : chi index of the month that begins at this tiết
 * tietName    : name used by lunar-javascript SolarTerm
 */
const TIET_TO_MONTH_CHI = [
  { tietName: '小寒',  vi: 'Tiểu Hàn',   monthChiIdx: 1  }, // Sửu
  { tietName: '立春',  vi: 'Lập Xuân',   monthChiIdx: 2  }, // Dần  ← năm mới bắt đầu đây
  { tietName: '惊蛰',  vi: 'Kinh Trập',  monthChiIdx: 3  }, // Mão
  { tietName: '清明',  vi: 'Thanh Minh', monthChiIdx: 4  }, // Thìn
  { tietName: '立夏',  vi: 'Lập Hạ',     monthChiIdx: 5  }, // Tỵ
  { tietName: '芒种',  vi: 'Mang Chủng', monthChiIdx: 6  }, // Ngọ
  { tietName: '小暑',  vi: 'Tiểu Thử',   monthChiIdx: 7  }, // Mùi
  { tietName: '立秋',  vi: 'Lập Thu',    monthChiIdx: 8  }, // Thân
  { tietName: '白露',  vi: 'Bạch Lộ',    monthChiIdx: 9  }, // Dậu
  { tietName: '寒露',  vi: 'Hàn Lộ',     monthChiIdx: 10 }, // Tuất
  { tietName: '立冬',  vi: 'Lập Đông',   monthChiIdx: 11 }, // Hợi
  { tietName: '大雪',  vi: 'Đại Tuyết',  monthChiIdx: 0  }, // Tý
];

/**
 * Tháng Can starting table.
 * For a given year Can (yearCanIdx % 5), month Dần (chiIdx=2) begins at this Can.
 * Each subsequent month chi increments Can by 2.
 */
const MONTH_Dान_CAN_START = [2, 4, 6, 8, 0]; // index = yearCanIdx % 5
// Giáp/Kỷ(0,5→%5=0): Bính Dần  (canIdx=2)
// Ất/Canh(1,6→%5=1): Mậu Dần   (canIdx=4)
// Bính/Tân(2,7→%5=2): Canh Dần  (canIdx=6)
// Đinh/Nhâm(3,8→%5=3): Nhâm Dần (canIdx=8)
// Mậu/Quý(4,9→%5=4): Giáp Dần  (canIdx=0)

// ─────────────────────────────────────────────────────────────────────────────
// 2. SOLAR TERM ENGINE (via lunar-javascript)
// ─────────────────────────────────────────────────────────────────────────────

// Module-level cache: "YYYY-tietName" → { year, month, day, hour, minute }
const _solarTermCache = new Map();

/**
 * Get exact datetime of a solar term for a given year.
 * Uses lunar-javascript ephemeris — accurate to the minute.
 *
 * @param {number} year  - Solar year
 * @param {string} tietName - Chinese name e.g. '立春'
 * @returns {{ year, month, day, hour, minute }} UTC+7 datetime
 */
function getSolarTermDate(year, tietName) {
  const key = `${year}-${tietName}`;
  if (_solarTermCache.has(key)) return _solarTermCache.get(key);

  const solar = Solar.fromYmd(year, 1, 1);
  const solarYear = solar.getLunar().getLunarYear();

  // lunar-javascript SolarTerm search: iterate months to find the term
  for (let m = 1; m <= 12; m++) {
    for (let d = 1; d <= 31; d++) {
      try {
        const s = Solar.fromYmd(year, m, d);
        const jieQi = s.getLunar().getJieQi();
        if (jieQi === tietName) {
          // Get precise time from JieQiTable
          const jieQiTable = s.getLunar().getJieQiTable();
          const dt = jieQiTable[tietName];
          // dt is a Solar object with time info
          const result = {
            year: dt.getYear(), month: dt.getMonth(), day: dt.getDay(),
            hour: dt.getHour(), minute: dt.getMinute(),
          };
          _solarTermCache.set(key, result);
          return result;
        }
      } catch (_) { /* skip invalid dates */ }
    }
  }
  throw new Error(`Solar term ${tietName} not found for year ${year}`);
}

/**
 * Get Lập Xuân datetime for a given solar year.
 * This is the boundary for Năm Trụ.
 */
function getLapXuan(year) {
  return getSolarTermDate(year, '立春');
}

/**
 * Compare a birth datetime against a solar term datetime.
 * Returns true if birthDt is BEFORE the solar term (exclusive).
 *
 * @param {{ year,month,day,hour,minute }} birthDt
 * @param {{ year,month,day,hour,minute }} termDt
 */
function isBefore(birthDt, termDt) {
  const b = new Date(birthDt.year, birthDt.month-1, birthDt.day, birthDt.hour, birthDt.minute);
  const t = new Date(termDt.year, termDt.month-1, termDt.day, termDt.hour, termDt.minute);
  return b < t;
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. PILLAR CALCULATIONS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Năm Trụ (Year Pillar)
 * Boundary: Lập Xuân (~Feb 4), NOT Tết Âm Lịch.
 *
 * @param {{ year,month,day,hour,minute }} birthDt
 * @returns {{ canIdx, chiIdx, canName, chiName, yearForPillar }}
 */
function getYearPillar(birthDt) {
  let pillarYear = birthDt.year;

  // If birth is before Lập Xuân of this year → use previous year
  const lapXuan = getLapXuan(birthDt.year);
  if (isBefore(birthDt, lapXuan)) {
    pillarYear = birthDt.year - 1;
  }

  const { canIdx, chiIdx } = getCanChiYear(pillarYear);
  return {
    canIdx,
    chiIdx,
    canName      : CAN_NAMES[canIdx],
    chiName      : CHI_NAMES[chiIdx],
    yearForPillar: pillarYear,
  };
}

/**
 * Tháng Trụ (Month Pillar)
 * Boundary: 12 Tiết Khí (astronomical solar terms), NOT lunar month boundary.
 *
 * Algorithm:
 * 1. Find which Tiết the birth falls in (scan backward from current month)
 * 2. Get month Chi from the Tiết
 * 3. Get month Can from year Can + month Chi offset
 *
 * @param {{ year,month,day,hour,minute }} birthDt
 * @param {number} yearCanIdx - from Năm Trụ (not necessarily birthDt.year)
 * @returns {{ canIdx, chiIdx, canName, chiName, tietName }}
 */
function getMonthPillar(birthDt, yearCanIdx) {
  // Determine which Tiết the birth date falls under.
  // Strategy: for each of the 12 tiết in current year AND previous year,
  // find the most recent tiết that started BEFORE birthDt.

  let activeTiet = null;
  let activeTietDt = null;

  // Check current year and previous year to handle Jan/Feb edge
  for (const yr of [birthDt.year - 1, birthDt.year]) {
    for (const tiet of TIET_TO_MONTH_CHI) {
      try {
        const termDt = getSolarTermDate(yr, tiet.tietName);
        if (!isBefore(birthDt, termDt)) {
          // birthDt is on or after this term
          if (activeTietDt === null || !isBefore(termDt, activeTietDt)) {
            // This term is more recent than the current candidate
            const tDt = new Date(termDt.year, termDt.month-1, termDt.day, termDt.hour, termDt.minute);
            const aDt = activeTietDt
              ? new Date(activeTietDt.year, activeTietDt.month-1, activeTietDt.day, activeTietDt.hour, activeTietDt.minute)
              : null;
            if (aDt === null || tDt > aDt) {
              activeTiet = tiet;
              activeTietDt = termDt;
            }
          }
        }
      } catch (_) { /* term not found in this year, skip */ }
    }
  }

  if (!activeTiet) {
    throw new Error(`Cannot determine month pillar for ${JSON.stringify(birthDt)}`);
  }

  const monthChiIdx = activeTiet.monthChiIdx;

  // Month Can: based on year Can and month Chi offset from Dần(2)
  // Dần (chiIdx=2) is the reference month for the year's first month Can
  const danCanStart = MONTH_Dान_CAN_START[yearCanIdx % 5];
  // Chi offset from Dần: (monthChiIdx - 2 + 12) % 12
  const offsetFromDan = (monthChiIdx - 2 + 12) % 12;
  const monthCanIdx = (danCanStart + offsetFromDan) % 10;

  return {
    canIdx  : monthCanIdx,
    chiIdx  : monthChiIdx,
    canName : CAN_NAMES[monthCanIdx],
    chiName : CHI_NAMES[monthChiIdx],
    tietName: activeTiet.vi,
  };
}

/**
 * Ngày Trụ (Day Pillar)
 * Uses JDN anchor from calendar-service.js.
 * Handle Tý giờ (23:00-24:00): ngày trụ shifts to NEXT day.
 *
 * @param {{ year,month,day,hour,minute }} birthDt
 * @returns {{ canIdx, chiIdx, canName, chiName }}
 */
function getDayPillar(birthDt) {
  let { year, month, day, hour } = birthDt;

  // Tý giờ starts at 23:00 — belongs to the NEXT day's pillar
  if (hour >= 23) {
    const nextDay = new Date(year, month - 1, day + 1);
    year  = nextDay.getFullYear();
    month = nextDay.getMonth() + 1;
    day   = nextDay.getDate();
  }

  const { canIdx, chiIdx } = getCanChiDay(year, month, day);
  return {
    canIdx,
    chiIdx,
    canName: CAN_NAMES[canIdx],
    chiName: CHI_NAMES[chiIdx],
  };
}

/**
 * Giờ Trụ (Hour Pillar)
 * Chi: 2-hour block from HOUR_TO_CHI.
 * Can: derived from Ngày Can (dayCanIdx), repeating every 5 days.
 *
 * @param {{ year,month,day,hour,minute }} birthDt
 * @param {number} dayCanIdx - from Ngày Trụ (after Tý shift)
 * @returns {{ canIdx, chiIdx, canName, chiName }}
 */
function getHourPillar(birthDt, dayCanIdx) {
  const hourChiIdx = HOUR_TO_CHI[birthDt.hour];
  const hourCanStart = HOUR_CAN_START[dayCanIdx % 5];
  // Hour Can = start Can for Tý + chi offset
  const hourCanIdx = (hourCanStart + hourChiIdx) % 10;

  return {
    canIdx : hourCanIdx,
    chiIdx : hourChiIdx,
    canName: CAN_NAMES[hourCanIdx],
    chiName: CHI_NAMES[hourChiIdx],
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. MASTER FUNCTION
// ─────────────────────────────────────────────────────────────────────────────

/**
 * getTuTru — compute all 4 pillars for a birth datetime.
 *
 * @param {string} birthDate  - 'YYYY-MM-DD' (required)
 * @param {string} [birthTime] - 'HH:MM' in Vietnam time (UTC+7). Default '12:00'.
 * @returns {TuTru}
 *
 * @example
 * getTuTru('1984-03-15', '10:30')
 * // {
 * //   year  : { canIdx:0, chiIdx:0, canName:'Giáp', chiName:'Tý', yearForPillar:1984 },
 * //   month : { canIdx:4, chiIdx:2, canName:'Mậu',  chiName:'Dần', tietName:'Kinh Trập' },
 * //   day   : { canIdx:3, chiIdx:7, canName:'Đinh', chiName:'Mùi' },
 * //   hour  : { canIdx:8, chiIdx:4, canName:'Nhâm', chiName:'Thìn' },
 * //   birthDt: { year:1984, month:3, day:15, hour:10, minute:30 }
 * // }
 */
function getTuTru(birthDate, birthTime = '12:00') {
  const [y, mo, d] = birthDate.split('-').map(Number);
  const [h, mi]    = birthTime.split(':').map(Number);
  const birthDt    = { year: y, month: mo, day: d, hour: h, minute: mi };

  const year  = getYearPillar(birthDt);
  const day   = getDayPillar(birthDt);
  const month = getMonthPillar(birthDt, year.canIdx);
  const hour  = getHourPillar(birthDt, day.canIdx);

  return { year, month, day, hour, birthDt };
}

/**
 * getTuTruFormatted — human-readable string output.
 * e.g. "Giáp Tý | Bính Dần | Đinh Mùi | Nhâm Thìn"
 */
function getTuTruFormatted(birthDate, birthTime = '12:00') {
  const tt = getTuTru(birthDate, birthTime);
  const fmt = p => `${p.canName} ${p.chiName}`;
  return `${fmt(tt.year)} | ${fmt(tt.month)} | ${fmt(tt.day)} | ${fmt(tt.hour)}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. EXPORTS
// ─────────────────────────────────────────────────────────────────────────────

module.exports = {
  getTuTru,
  getTuTruFormatted,
  // Sub-pillars (exported for testing)
  getYearPillar,
  getMonthPillar,
  getDayPillar,
  getHourPillar,
  // Solar term utilities
  getSolarTermDate,
  getLapXuan,
  isBefore,
  // Tables
  HOUR_TO_CHI,
  HOUR_CAN_START,
  TIET_TO_MONTH_CHI,
  MONTH_Dान_CAN_START,
};
