/**
 * scoring.js
 *
 * Layer 3: Intent-aware scoring engine.
 *
 * Input:  dayInfo    (from calendar-service.getDayInfo)
 *         userChart  (from calendar-service.getUserChart)
 *         intent     (string enum)
 *         intentRules (loaded from docs/seed/intent-rules.json)
 *
 * Output: ScoreResult {
 *   score      : number   — 0..100+
 *   grade      : 'A'|'B'|'C'|'D'
 *   bonusSao   : string[] — active cát tinh for this intent
 *   penaltySao : string[] — active hung tinh for this intent
 *   reasons_vi : string[] — display text for UI
 * }
 *
 * ─── THREE SPECIAL RULES ─────────────────────────────────────────────────────
 *
 * SPECIAL RULE 1 — Ngoại lệ Nguyệt Đức cho KIEN_TUNG
 *   Ngọc Hạp Thông Thư: "Nguyệt Đức: Trừ tố tụng thì những việc khác đều tốt."
 *   Implementation: When intent === KIEN_TUNG, hasNguyetDuc bonus is SKIPPED
 *   even though Nguyệt Đức is normally a universal cát tinh.
 *   See: _applyNguyetDucBonus()
 *
 * SPECIAL RULE 2 — Thiên Xá nghịch lý
 *   Ngọc Hạp Thông Thư: "Thiên Xá: Tốt cho tế tự, giải oan. KỴ động thổ, nhập trạch."
 *   Same sao (Thiên Xá) is a BONUS for TE_TU, GIAI_HAN, AN_TANG, CAU_TU
 *   but a PENALTY for DONG_THO, NHAP_TRACH, LAM_NHA, DAO_GIENG.
 *   See: THIEN_XA_BONUS_INTENTS / THIEN_XA_PENALTY_INTENTS
 *
 * SPECIAL RULE 3 — Tháng Cô Hồn → handled upstream in filter.js (Layer 2).
 *   Dates blocked by Cô Hồn never reach scoring.js.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 */

'use strict';

// ─────────────────────────────────────────────────────────────────────────────
// SPECIAL RULE 2 LOOKUP TABLES
// Thiên Xá: tốt cho các việc tâm linh, KỴ các việc đất/xây dựng
// ─────────────────────────────────────────────────────────────────────────────

const THIEN_XA_BONUS_INTENTS = new Set([
  'TE_TU',          // tế tự, cúng bái — tốt nhất
  'GIAI_HAN',       // giải hạn, cúng sao
  'AN_TANG',        // an táng (xá tội, giải oan cho người đã khuất)
  'CAI_TANG',       // cải táng
  'CAU_TU',         // cầu tự, cầu con (cầu phúc tại đền chùa)
  'KIEN_TUNG',      // giải oan, tố tụng
  'KHAM_BENH',      // khám bệnh, chữa bệnh
]);

const THIEN_XA_PENALTY_INTENTS = new Set([
  'DONG_THO',       // kỵ động thổ — rule nguyên văn Ngọc Hạp
  'NHAP_TRACH',     // kỵ nhập trạch — rule nguyên văn Ngọc Hạp
  'LAM_NHA',        // kỵ khởi tạo xây dựng
  'DAO_GIENG',      // kỵ đào đất
  'XAY_BEP',        // kỵ sửa bếp (liên quan đất/xây dựng)
]);

// ─────────────────────────────────────────────────────────────────────────────
// SCORING CONSTANTS
// ─────────────────────────────────────────────────────────────────────────────

const BASE_SCORE = 50;

const TRUC_SCORE_MULTIPLIER = 10; // trucScore (-2..+2) × 10 = -20..+20

const BONUS = {
  thienDuc     : 15,
  thienDucHop  : 10,
  nguyetDuc    : 12,
  nguyetDucHop :  8,
  duongThanMatch: 12,   // dayNapAmHanh === user.duongThan
  intentBonus  :  8,    // per matching bonus_sao in intent rule
  thienXaBonus :  8,    // Thiên Xá bonus for eligible intents (Rule 2)
  trucPreferred: 15,    // intent preferred_truc match
};

const PENALTY = {
  canKhac      : -8,    // severity 2 from filter.js
  kyThanMatch  : -10,   // dayNapAmHanh === user.kyThan
  intentPenalty: -15,   // per matching forbidden_sao
  thienXaPenalty: -15,  // Thiên Xá penalty for ineligible intents (Rule 2)
  layer2Severity2: -5,  // additional general penalty when filter.severity === 2
  trucForbidden: -20,   // intent forbidden_truc match
};

const GRADE_THRESHOLDS = { A: 80, B: 65, C: 50 };

// ─────────────────────────────────────────────────────────────────────────────
// SAO NGÀY DETECTOR MAP
// Maps sao key names (used in intent-rules.json) → dayInfo boolean field or
// a compute function (dayInfo, userChart) → boolean
//
// Add new sao here as the engine expands.
// ─────────────────────────────────────────────────────────────────────────────

const SAO_DETECTORS = {
  // Universal cát tinh — already computed in calendar-service
  thienDuc       : (d) => d.hasThienDuc,
  thienDucHop    : (d) => d.hasThienDucHop,
  nguyetDuc      : (d) => d.hasNguyetDuc,
  nguyetDucHop   : (d) => d.hasNguyetDucHop,

  // Personal cát tinh — compared against user chart
  duongThanMatch : (d, u) => d.dayNapAmHanh === u.duongThan,

  // Hung tinh — Layer 1 flags (already caused discard if triggered,
  // but Tam Nương severity varies by intent so we re-expose here)
  tamNuong       : (d) => d.isTamNuong,
  nguyetKy       : (d) => d.isNguyetKy,
  duongCongKy    : (d) => d.isDuongCongKy,

  // Thiên Xá — NOT a simple boolean: handled separately via Rule 2
  // Detector returns true if the day IS Thiên Xá.
  // Scoring logic then checks THIEN_XA_BONUS/PENALTY_INTENTS to decide direction.
  thienXa        : (d) => d.hasThienXa || false,  // placeholder — set by enrichDayInfo if available

  // Placeholder detectors for sao not yet computed in calendar-service.
  // Return false until calendar-service is extended.
  // SME must verify computation method before enabling.
  sinhKhi        : (d) => d.hasSinhKhi        || false,
  thienHy        : (d) => d.hasThienHy        || false,
  thienPhu       : (d) => d.hasThienPhu       || false,
  thienTai       : (d) => d.hasThienTai       || false,
  diaTai         : (d) => d.hasDiaTai         || false,
  nguyetTai      : (d) => d.hasNguyetTai      || false,
  locKho         : (d) => d.hasLocKho         || false,
  thienMa        : (d) => d.hasThienMa        || false,
  dichMa         : (d) => d.hasDichMa         || false,
  phoHo          : (d) => d.hasPhoHo          || false,
  ichHau         : (d) => d.hasIchHau         || false,
  tucThe         : (d) => d.hasTucThe         || false,
  yeuYen         : (d) => d.hasYeuYen         || false,
  nguyetKhong    : (d) => d.hasNguyetKhong    || false,
  giaiThan       : (d) => d.hasGiaiThan       || false,
  thanhTam       : (d) => d.hasThanhTam       || false,
  thienQuan      : (d) => d.hasThienQuan      || false,
  thienQuy       : (d) => d.hasThienQuy       || false,
  thienPhuc      : (d) => d.hasThienPhuc      || false,
  thienAn        : (d) => d.hasThienAn        || false,
  mauThuong      : (d) => d.hasMauThuong      || false,
  phucHau        : (d) => d.hasPhucHau        || false,
  catKhanh       : (d) => d.hasCatKhanh       || false,

  // Hung tinh placeholders
  thienTac       : (d) => d.hasThienTac       || false,
  diaTac         : (d) => d.hasDiaTac         || false,
  thienCuong     : (d) => d.hasThienCuong     || false,
  daiHao         : (d) => d.hasDaiHao         || false,
  tieuHao        : (d) => d.hasTieuHao        || false,
  nguyetSat      : (d) => d.hasNguyetSat      || false,
  nguyetHoa      : (d) => d.hasNguyetHoa      || false,
  thoOn          : (d) => d.hasThoOn          || false,
  thoPhu         : (d) => d.hasThoPhu         || false,
  thoPhU         : (d) => d.hasThoPhu         || false,  // alias — intent-rules.json uses "thoPhU"
  thoCam         : (d) => d.hasThoCam         || false,
  cuuThoQuy      : (d) => d.hasCuuThoQuy      || false,
  thoTu          : (d) => d.hasThoTu          || false,
  satChu         : (d) => d.hasSatChu         || false,
  hoaTai         : (d) => d.hasHoaTai         || false,
  nguyetYemDaiHoa: (d) => d.hasNguyetYemDaiHoa|| false,
  vatVong        : (d) => d.hasVatVong        || false,
  cuuKhong       : (d) => d.hasCuuKhong       || false,
  lucBatThanh    : (d) => d.hasLucBatThanh    || false,
  nhanCach       : (d) => d.hasNhanCach       || false,
  phiMaSat       : (d) => d.hasPhiMaSat       || false,
  hoangSa        : (d) => d.hasHoangSa        || false,
  nguNguyQuiet   : (d) => d.hasNguNguyQuiet   || false,
  thanCach       : (d) => d.hasThanCach       || false,
  trungTang      : (d) => d.hasTrungTang      || false,
  haKhoiCauGiao  : (d) => d.hasHaKhoiCauGiao  || false,
  loiCong        : (d) => d.hasLoiCong        || false,
  thienNgucThienHoa: (d) => d.hasThienNgucThienHoa || false,

  // Additional detectors referenced in intent-rules.json
  diaPha         : (d) => d.hasDiaPha         || false,
  kinhTam        : (d) => d.hasKinhTam        || false,
  lucHop         : (d) => d.hasLucHop         || false,
  minhTinh       : (d) => d.hasMinhTinh       || false,
  nguyetAn       : (d) => d.hasNguyetAn       || false,
  nguyetHoaDockHoa: (d) => d.hasNguyetHoaDockHoa || false,
  nguyetKienChuyenSat: (d) => d.hasNguyetKienChuyenSat || false,
  phucSinh       : (d) => d.hasPhucSinh       || false,
  quyCoc         : (d) => d.hasQuyCoc         || false,
  tamHop         : (d) => d.hasTamHop         || false,
  thienDiaChuyenSat: (d) => d.hasThienDiaChuyenSat || false,
  thienThanh     : (d) => d.hasThienThanh     || false,
};

// ─────────────────────────────────────────────────────────────────────────────
// SPECIAL RULE 1 HELPER
// Nguyệt Đức ngoại lệ: không bonus cho KIEN_TUNG
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Returns true if Nguyệt Đức bonus should apply for this intent.
 *
 * SPECIAL RULE 1: Ngọc Hạp Thông Thư states:
 *   "Nguyệt Đức: Trừ tố tụng thì những việc khác đều tốt."
 * Therefore, KIEN_TUNG is excluded from Nguyệt Đức bonus.
 */
function _nguyetDucBonusApplies(intent) {
  return intent !== 'KIEN_TUNG';
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN SCORING FUNCTION
// ─────────────────────────────────────────────────────────────────────────────

/**
 * computeScore
 *
 * @param {object} dayInfo      - from calendar-service.getDayInfo()
 * @param {object} userChart    - from calendar-service.getUserChart()
 * @param {string} intent       - intent enum
 * @param {object} intentRule   - single intent entry from intent-rules.json
 * @param {object} filterResult - from filter.applyLayer2Filter()
 * @returns {ScoreResult}
 */
function computeScore(dayInfo, userChart, intent, intentRule, filterResult) {
  let score = BASE_SCORE;
  const bonusSao   = [];
  const penaltySao = [];
  const reasons    = [];

  // ── 1. Trực score ──────────────────────────────────────────────────────────
  const trucDelta = dayInfo.trucScore * TRUC_SCORE_MULTIPLIER;
  score += trucDelta;
  if (trucDelta > 0) {
    reasons.push(`Trực ${dayInfo.trucName} — ngày tốt (+${trucDelta})`);
  } else if (trucDelta < 0) {
    reasons.push(`Trực ${dayInfo.trucName} — ngày xấu (${trucDelta})`);
  }

  // ── 1b. Trực intent preference ───────────────────────────────────────────
  const preferredTruc = intentRule.preferred_truc || [];
  const forbiddenTruc = intentRule.forbidden_truc || [];
  const trucIdx = dayInfo.trucIdx;
  if (trucIdx !== undefined) {
    if (preferredTruc.includes(trucIdx)) {
      score += BONUS.trucPreferred;
      reasons.push(
        `Trực ${dayInfo.trucName} — hợp cho ${_intentLabel(intent)} (+${BONUS.trucPreferred})`
      );
    } else if (forbiddenTruc.includes(trucIdx)) {
      score += PENALTY.trucForbidden;
      reasons.push(
        `Trực ${dayInfo.trucName} — kỵ ${_intentLabel(intent)} (${PENALTY.trucForbidden})`
      );
    }
  }

  // ── 2. Universal cát tinh ─────────────────────────────────────────────────

  if (dayInfo.hasThienDuc) {
    score += BONUS.thienDuc;
    bonusSao.push('Thiên Đức');
    reasons.push(`Ngày có Thiên Đức (+${BONUS.thienDuc})`);
  }
  if (dayInfo.hasThienDucHop) {
    score += BONUS.thienDucHop;
    bonusSao.push('Thiên Đức Hợp');
    reasons.push(`Ngày có Thiên Đức Hợp (+${BONUS.thienDucHop})`);
  }

  // ── SPECIAL RULE 1: Nguyệt Đức ngoại lệ KIEN_TUNG ────────────────────────
  if (dayInfo.hasNguyetDuc) {
    if (_nguyetDucBonusApplies(intent)) {
      score += BONUS.nguyetDuc;
      bonusSao.push('Nguyệt Đức');
      reasons.push(`Ngày có Nguyệt Đức (+${BONUS.nguyetDuc})`);
    } else {
      // Nguyệt Đức có nhưng không tính điểm cho kiện tụng
      reasons.push(`Nguyệt Đức — không tính điểm cho ${_intentLabel(intent)} (theo Ngọc Hạp Thông Thư)`);
    }
  }
  if (dayInfo.hasNguyetDucHop) {
    if (_nguyetDucBonusApplies(intent)) {
      score += BONUS.nguyetDucHop;
      bonusSao.push('Nguyệt Đức Hợp');
      reasons.push(`Ngày có Nguyệt Đức Hợp (+${BONUS.nguyetDucHop})`);
    } else {
      reasons.push(`Nguyệt Đức Hợp — không tính điểm cho ${_intentLabel(intent)} (theo Ngọc Hạp Thông Thư)`);
    }
  }

  // ── 3. Dương Thần element match ────────────────────────────────────────────
  if (dayInfo.dayNapAmHanh === userChart.duongThan) {
    score += BONUS.duongThanMatch;
    reasons.push(
      `Nạp Âm ngày (${dayInfo.dayNapAmHanh}) là Dương Thần của mệnh ${userChart.menhName} (+${BONUS.duongThanMatch})`
    );
  }

  // ── 4. Layer 2 severity penalty ────────────────────────────────────────────
  if (filterResult.severity === 2) {
    score += PENALTY.layer2Severity2;
    filterResult.reasons.forEach(r => reasons.push(r + ` (${PENALTY.layer2Severity2})`));
  }

  // ── 5. SPECIAL RULE 2: Thiên Xá nghịch lý ─────────────────────────────────
  // "Tốt cho tế tự, giải oan — KỴ động thổ, nhập trạch"
  if (SAO_DETECTORS.thienXa(dayInfo)) {
    if (THIEN_XA_BONUS_INTENTS.has(intent)) {
      score += BONUS.thienXaBonus;
      bonusSao.push('Thiên Xá');
      reasons.push(
        `Ngày có Thiên Xá — cát tinh cho ${_intentLabel(intent)} (+${BONUS.thienXaBonus})`
      );
    } else if (THIEN_XA_PENALTY_INTENTS.has(intent)) {
      score += PENALTY.thienXaPenalty;
      penaltySao.push('Thiên Xá');
      reasons.push(
        `Ngày có Thiên Xá — KỴ ${_intentLabel(intent)} theo Ngọc Hạp Thông Thư (${PENALTY.thienXaPenalty})`
      );
    }
    // Neutral intents: no bonus/penalty (skip silently)
  }

  // ── 6. Intent-specific bonus_sao ──────────────────────────────────────────
  const ruleBonusSao = intentRule.bonus_sao || [];
  for (const saoKey of ruleBonusSao) {
    // Skip Thiên Xá here — already handled above by Rule 2
    if (saoKey === 'thienXa') continue;
    // Skip Nguyệt Đức family — already handled above by Rule 1
    if (saoKey === 'nguyetDuc' || saoKey === 'nguyetDucHop') continue;
    // Skip universal sao already scored above
    if (saoKey === 'thienDuc' || saoKey === 'thienDucHop') continue;

    const detector = SAO_DETECTORS[saoKey];
    if (!detector) continue; // unknown sao — skip

    if (detector(dayInfo, userChart)) {
      score += BONUS.intentBonus;
      bonusSao.push(_saoLabel(saoKey));
      reasons.push(`Cát tinh ${_saoLabel(saoKey)} — tốt cho ${_intentLabel(intent)} (+${BONUS.intentBonus})`);
    }
  }

  // ── 7. Intent-specific forbidden_sao ──────────────────────────────────────
  const ruleForbiddenSao = intentRule.forbidden_sao || [];
  for (const saoKey of ruleForbiddenSao) {
    // Thiên Xá handled by Rule 2 above — skip here
    if (saoKey === 'thienXa') continue;

    const detector = SAO_DETECTORS[saoKey];
    if (!detector) continue;

    if (detector(dayInfo, userChart)) {
      // Special: Tam Nương severity 3 for DAM_CUOI/AN_HOI → hard discard signal
      // (Layer 1 already discards Tam Nương universally, but we add penalty
      //  in case intent-specific severity override is needed in future)
      score += PENALTY.intentPenalty;
      penaltySao.push(_saoLabel(saoKey));
      reasons.push(`Hung tinh ${_saoLabel(saoKey)} — kỵ ${_intentLabel(intent)} (${PENALTY.intentPenalty})`);
    }
  }

  // ── 8. Grade ───────────────────────────────────────────────────────────────
  const grade = score >= GRADE_THRESHOLDS.A ? 'A'
              : score >= GRADE_THRESHOLDS.B ? 'B'
              : score >= GRADE_THRESHOLDS.C ? 'C'
              : 'D';

  return {
    score,
    grade,
    bonusSao,
    penaltySao,
    reasons_vi: reasons,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// LABEL HELPERS
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

const SAO_LABELS = {
  thienDuc   : 'Thiên Đức',   thienDucHop : 'Thiên Đức Hợp',
  nguyetDuc  : 'Nguyệt Đức',  nguyetDucHop: 'Nguyệt Đức Hợp',
  thienXa    : 'Thiên Xá',    sinhKhi     : 'Sinh Khí',
  thienHy    : 'Thiên Hỷ',    thienPhu    : 'Thiên Phú',
  thienTai   : 'Thiên Tài',   diaTai      : 'Địa Tài',
  nguyetTai  : 'Nguyệt Tài',  locKho      : 'Lộc Khố',
  thienMa    : 'Thiên Mã',    dichMa      : 'Dịch Mã',
  phoHo      : 'Phổ Hộ',      ichHau      : 'Ích Hậu',
  tucThe     : 'Tục Thế',     yeuYen      : 'Yếu Yên',
  nguyetKhong: 'Nguyệt Không', giaiThan   : 'Giải Thần',
  thanhTam   : 'Thánh Tâm',   thienQuan   : 'Thiên Quan',
  thienQuy   : 'Thiên Quý',   thienPhuc   : 'Thiên Phúc',
  thienAn    : 'Thiên Ân',    mauThuong   : 'Mậu Thương',
  phucHau    : 'Phúc Hậu',    catKhanh    : 'Cát Khánh',
  tamNuong   : 'Tam Nương',   nguyetKy    : 'Nguyệt Kỵ',
  duongCongKy: 'Dương Công Kỵ', thienTac  : 'Thiên Tặc',
  diaTac     : 'Địa Tặc',     thienCuong  : 'Thiên Cương',
  daiHao     : 'Đại Hao',     tieuHao     : 'Tiểu Hao',
  nguyetSat  : 'Nguyệt Sát',  nguyetHoa   : 'Nguyệt Hỏa',
  thoOn      : 'Thổ Ôn',      thoPhu      : 'Thổ Phủ',
  thoCam     : 'Thổ Cấm',     cuuThoQuy   : 'Cửu Thổ Quỷ',
  thoTu      : 'Thọ Tử',      satChu      : 'Sát Chủ',
  hoaTai     : 'Hỏa Tai',     vatVong     : 'Vãng Vong',
  cuuKhong   : 'Cửu Không',   lucBatThanh : 'Lục Bất Thành',
  nhanCach   : 'Nhân Cách',   phiMaSat    : 'Phi Ma Sát',
  hoangSa    : 'Hoàng Sa',    thanCach    : 'Thần Cách',
  trungTang  : 'Trùng Tang',  haKhoiCauGiao: 'Hà Khôi Câu Giảo',
  loiCong    : 'Lôi Công',    thienNgucThienHoa: 'Thiên Ngục Thiên Hỏa',
  nguyetYemDaiHoa: 'Nguyệt Yếm Đại Họa',
  nguNguyQuiet: 'Ngũ Quỷ',
  diaPha     : 'Địa Phá',
  kinhTam    : 'Kinh Tâm',
  lucHop     : 'Lục Hợp',
  minhTinh   : 'Minh Tinh',
  nguyetAn   : 'Nguyệt Ân',
  nguyetHoaDockHoa: 'Nguyệt Hỏa Độc Hỏa',
  nguyetKienChuyenSat: 'Nguyệt Kiến Chuyển Sát',
  phucSinh   : 'Phục Sinh',
  quyCoc     : 'Quỷ Cốc',
  tamHop     : 'Tam Hợp',
  thienDiaChuyenSat: 'Thiên Địa Chuyển Sát',
  thienThanh : 'Thiên Thành',
};

function _intentLabel(intent) {
  return INTENT_LABELS[intent] || intent;
}

function _saoLabel(key) {
  return SAO_LABELS[key] || key;
}

// ─────────────────────────────────────────────────────────────────────────────
// EXPORTS
// ─────────────────────────────────────────────────────────────────────────────

module.exports = {
  computeScore,
  // Exported for testing & documentation
  THIEN_XA_BONUS_INTENTS,
  THIEN_XA_PENALTY_INTENTS,
  BASE_SCORE,
  GRADE_THRESHOLDS,
};
