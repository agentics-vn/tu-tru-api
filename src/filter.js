/**
 * filter.js
 *
 * Layer 2: Personal chart + intent-specific date filter.
 *
 * Input:  dayInfo   (from calendar-service.getDayInfo)
 *         userChart (from calendar-service.getUserChart)
 *         intent    (string enum)
 *
 * Output: FilterResult {
 *   pass     : boolean   — false = discard this date entirely
 *   severity : 0 | 2 | 3
 *   reasons  : string[]  — human-readable (Vietnamese) reason codes
 * }
 *
 * Rules:
 *   R1  Severity 3 — Địa Chi Tương Xung          → DISCARD
 *   R2  Severity 2 — Thiên Can Tương Khắc         → AVOID (still returned, score penalized)
 *   R3  Severity 2 — Ngày có hành Kỵ Thần         → AVOID
 *   R4  Severity 3 — Tháng Cô Hồn (tháng 7 AL)   → DISCARD (intent-specific)  ← SPECIAL RULE 3
 *
 * NOTE: Layer 1 filters (Nguyệt Kỵ, Tam Nương, Dương Công Kỵ, Trực Phá/Nguy)
 * are applied by calendar-service.js before this layer is called.
 * This layer only receives dates where dayInfo.isLayer1Pass === true.
 *
 * Source: docs/algorithm.md §Layer2
 */

'use strict';

const { isXung, isCanKhac } = require('./calendar-service');

// ─────────────────────────────────────────────────────────────────────────────
// SPECIAL RULE 3: Tháng Cô Hồn (lunar month 7) blocked intents
// These intents cannot proceed in tháng 7 âm lịch regardless of other factors.
// Source: Ngọc Hạp Thông Thư — kiêng đại sự tháng Cô Hồn
// ─────────────────────────────────────────────────────────────────────────────

const COHON_BLOCKED_INTENTS = new Set([
  'DAM_CUOI',       // Đám cưới — tuyệt đối không tổ chức tháng 7
  'AN_HOI',         // Ăn hỏi — kiêng tháng Cô Hồn
  'DONG_THO',       // Động thổ — khởi công tháng Cô Hồn dễ gặp trắc trở
  'NHAP_TRACH',     // Nhập trạch — vào nhà tháng Cô Hồn không tốt
  'LAM_NHA',        // Làm nhà — kiêng khởi sự xây dựng
  'MUA_NHA_DAT',    // Mua nhà đất — ký hợp đồng bất động sản
  'KHAI_TRUONG',    // Khai trương — mở hàng tháng Cô Hồn
]);

// ─────────────────────────────────────────────────────────────────────────────
// MAIN FILTER FUNCTION
// ─────────────────────────────────────────────────────────────────────────────

/**
 * applyLayer2Filter
 *
 * @param {object} dayInfo   - output of calendar-service.getDayInfo()
 * @param {object} userChart - output of calendar-service.getUserChart()
 * @param {string} intent    - intent enum string e.g. 'KHAI_TRUONG'
 * @returns {FilterResult}
 */
function applyLayer2Filter(dayInfo, userChart, intent) {
  const reasons = [];
  let maxSeverity = 0;

  // ── SPECIAL RULE 3: Tháng Cô Hồn ─────────────────────────────────────────
  // Must check BEFORE personal rules — this is a universal block for these intents.
  // isCohon flag is set in calendar-service.getDayInfo() when lunarMonth === 7.
  if (dayInfo.isCohon && COHON_BLOCKED_INTENTS.has(intent)) {
    return {
      pass    : false,
      severity: 3,
      reasons : ['Tháng Cô Hồn (tháng 7 âm lịch) — không thích hợp cho ' + _intentLabel(intent)],
    };
  }

  // ── R1: Địa Chi Tương Xung (severity 3 → DISCARD) ────────────────────────
  if (isXung(dayInfo.dayChiIdx, userChart.yearChiIdx)) {
    // Xung is a hard discard — no need to check further
    return {
      pass    : false,
      severity: 3,
      reasons : [
        `Địa Chi ngày ${dayInfo.dayChiName} xung với tuổi ${userChart.yearChiName}`,
      ],
    };
  }

  // ── R2: Thiên Can Tương Khắc (severity 2 → AVOID) ────────────────────────
  if (isCanKhac(dayInfo.dayCanIdx, userChart.yearCanIdx)) {
    maxSeverity = Math.max(maxSeverity, 2);
    reasons.push(
      `Thiên Can ngày ${dayInfo.dayCanName} khắc Thiên Can tuổi ${userChart.yearCanName}`
    );
  }

  // ── R3: Ngày có hành Kỵ Thần (severity 2 → AVOID) ────────────────────────
  // Per algorithm.md: compare Can's element (dayCanHanh), not Nạp Âm element
  if (dayInfo.dayCanHanh === userChart.kyThan) {
    maxSeverity = Math.max(maxSeverity, 2);
    reasons.push(
      `Hành Thiên Can ngày (${dayInfo.dayCanHanh}) là Kỵ Thần của mệnh ${userChart.menhName}`
    );
  }

  return {
    pass    : true,
    severity: maxSeverity,
    reasons,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────

const INTENT_LABELS = {
  KHAI_TRUONG    : 'Khai trương',
  KY_HOP_DONG    : 'Ký kết hợp đồng',
  AN_HOI         : 'Lễ ăn hỏi',
  DAM_CUOI       : 'Đám cưới',
  DONG_THO       : 'Động thổ',
  NHAP_TRACH     : 'Nhập trạch',
  LAM_NHA        : 'Làm nhà',
  AN_TANG        : 'An táng',
  CAI_TANG       : 'Cải táng',
  XUAT_HANH      : 'Xuất hành',
  CAU_TAI        : 'Cầu tài lộc',
  TE_TU          : 'Tế tự',
  KHAM_BENH      : 'Khám bệnh',
  PHAU_THUAT     : 'Phẫu thuật',
  NHAP_HOC_THI_CU: 'Nhập học / Thi cử',
  NHAM_CHUC      : 'Nhậm chức',
  MUA_NHA_DAT    : 'Mua nhà đất',
  DAO_GIENG      : 'Đào giếng',
  TRONG_CAY      : 'Trồng cây',
  CAU_TU         : 'Cầu tự',
  XAY_BEP        : 'Xây bếp',
  LAM_GIUONG     : 'Làm giường',
  KIEN_TUNG      : 'Kiện tụng',
  DI_CHUYEN_NGOAI: 'Xuất ngoại',
  GIAI_HAN       : 'Giải hạn',
  MAC_DINH       : 'Sự kiện chung',
};

function _intentLabel(intent) {
  return INTENT_LABELS[intent] || intent;
}

// ─────────────────────────────────────────────────────────────────────────────
// EXPORTS
// ─────────────────────────────────────────────────────────────────────────────

module.exports = {
  applyLayer2Filter,
  COHON_BLOCKED_INTENTS, // exported for testing
};
