/**
 * scoring.test.js
 *
 * Unit tests for scoring.js — focuses on the 3 special rules.
 *
 * Run: node src/scoring.test.js
 */

'use strict';

const { computeScore, THIEN_XA_BONUS_INTENTS, THIEN_XA_PENALTY_INTENTS } = require('./scoring');
const { applyLayer2Filter, COHON_BLOCKED_INTENTS } = require('./filter');

// ─── Minimal stubs ───────────────────────────────────────────────────────────

const BASE_CHART = {
  birthYear  : 1990,
  yearCanIdx : 6,  // Canh
  yearChiIdx : 6,  // Ngọ
  yearCanName: 'Canh',
  yearChiName: 'Ngọ',
  menhHanh   : 'Thổ',
  menhName   : 'Lộ Bàng Thổ',
  duongThan  : 'Hỏa',
  kyThan     : 'Mộc',
};

const BASE_DAY = {
  date           : '2026-03-15',
  dayCanIdx      : 0,   // Giáp
  dayChiIdx      : 11,  // Hợi (not Xung with Ngọ: |11-6|=5, not 6)
  dayCanName     : 'Giáp',
  dayChiName     : 'Hợi',
  dayNapAmHanh   : 'Thủy',
  lunarDay       : 18,
  lunarMonth     : 2,
  lunarYear      : 2026,
  isLeapMonth    : false,
  trucIdx        : 8,   // Thành
  trucName       : 'Thành',
  trucScore      : 2,
  hasThienDuc    : false,
  hasThienDucHop : false,
  hasNguyetDuc   : false,
  hasNguyetDucHop: false,
  isNguyetKy     : false,
  isTamNuong     : false,
  isDuongCongKy  : false,
  isTrucPha      : false,
  isTrucNguy     : false,
  isLayer1Pass   : true,
  isCohon        : false,
};

const BASE_FILTER = { pass: true, severity: 0, reasons: [] };

const BASE_RULE = {
  bonus_sao   : [],
  forbidden_sao: [],
};

// ─── Test runner ─────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✅  ${name}`);
    passed++;
  } catch (e) {
    console.log(`  ❌  ${name}`);
    console.log(`       ${e.message}`);
    failed++;
  }
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg || 'Assertion failed');
}

function assertEqual(a, b, msg) {
  if (a !== b) throw new Error(msg || `Expected ${b}, got ${a}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// SPECIAL RULE 1 TESTS — Nguyệt Đức ngoại lệ KIEN_TUNG
// ─────────────────────────────────────────────────────────────────────────────

console.log('\n── Special Rule 1: Nguyệt Đức ngoại lệ ───────────────────────────────────');

test('R1a: Nguyệt Đức adds +12 for KHAI_TRUONG', () => {
  const day = { ...BASE_DAY, hasNguyetDuc: true };
  const result = computeScore(day, BASE_CHART, 'KHAI_TRUONG', BASE_RULE, BASE_FILTER);
  // trucScore=2 → +20, nguyetDuc → +12 = base 50 + 20 + 12 = 82
  assertEqual(result.score, 82, `score=${result.score}`);
  assert(result.bonusSao.includes('Nguyệt Đức'), 'Nguyệt Đức should be in bonusSao');
});

test('R1b: Nguyệt Đức adds ZERO for KIEN_TUNG', () => {
  const day = { ...BASE_DAY, hasNguyetDuc: true };
  const result = computeScore(day, BASE_CHART, 'KIEN_TUNG', BASE_RULE, BASE_FILTER);
  // trucScore=2 → +20 = base 50 + 20 = 70 (no Nguyệt Đức bonus)
  assertEqual(result.score, 70, `score=${result.score}`);
  assert(!result.bonusSao.includes('Nguyệt Đức'), 'Nguyệt Đức should NOT be in bonusSao for KIEN_TUNG');
  assert(
    result.reasons_vi.some(r => r.includes('Nguyệt Đức') && r.includes('không tính điểm')),
    'Should explain why Nguyệt Đức is skipped'
  );
});

test('R1c: Nguyệt Đức Hợp also skipped for KIEN_TUNG', () => {
  const day = { ...BASE_DAY, hasNguyetDucHop: true };
  const resultKT  = computeScore(day, BASE_CHART, 'KIEN_TUNG', BASE_RULE, BASE_FILTER);
  const resultKTK = computeScore(day, BASE_CHART, 'KHAI_TRUONG', BASE_RULE, BASE_FILTER);
  assert(resultKT.score < resultKTK.score, 'KIEN_TUNG should score lower when Nguyệt Đức Hợp is present');
});

// ─────────────────────────────────────────────────────────────────────────────
// SPECIAL RULE 2 TESTS — Thiên Xá nghịch lý
// ─────────────────────────────────────────────────────────────────────────────

console.log('\n── Special Rule 2: Thiên Xá nghịch lý ────────────────────────────────────');

test('R2a: Thiên Xá is BONUS (+8) for TE_TU', () => {
  const day = { ...BASE_DAY, hasThienXa: true };
  const result = computeScore(day, BASE_CHART, 'TE_TU', BASE_RULE, BASE_FILTER);
  // base 50 + truc +20 + thienXa +8 = 78
  assertEqual(result.score, 78, `score=${result.score}`);
  assert(result.bonusSao.includes('Thiên Xá'), 'Thiên Xá should be in bonusSao for TE_TU');
});

test('R2b: Thiên Xá is PENALTY (-15) for DONG_THO', () => {
  const day = { ...BASE_DAY, hasThienXa: true };
  const result = computeScore(day, BASE_CHART, 'DONG_THO', BASE_RULE, BASE_FILTER);
  // base 50 + truc +20 + thienXa -15 = 55
  assertEqual(result.score, 55, `score=${result.score}`);
  assert(result.penaltySao.includes('Thiên Xá'), 'Thiên Xá should be in penaltySao for DONG_THO');
  assert(
    result.reasons_vi.some(r => r.includes('KỴ') && r.includes('Thiên Xá')),
    'Should explain Thiên Xá kỵ message'
  );
});

test('R2c: Thiên Xá is PENALTY for NHAP_TRACH', () => {
  const day = { ...BASE_DAY, hasThienXa: true };
  const result = computeScore(day, BASE_CHART, 'NHAP_TRACH', BASE_RULE, BASE_FILTER);
  assert(result.penaltySao.includes('Thiên Xá'), 'Thiên Xá should penalize NHAP_TRACH');
});

test('R2d: Thiên Xá is BONUS for GIAI_HAN', () => {
  const day = { ...BASE_DAY, hasThienXa: true };
  const result = computeScore(day, BASE_CHART, 'GIAI_HAN', BASE_RULE, BASE_FILTER);
  assert(result.bonusSao.includes('Thiên Xá'), 'Thiên Xá should bonus GIAI_HAN');
});

test('R2e: Thiên Xá is NEUTRAL (no effect) for XUAT_HANH', () => {
  const dayWith    = { ...BASE_DAY, hasThienXa: true  };
  const dayWithout = { ...BASE_DAY, hasThienXa: false };
  const scoreWith    = computeScore(dayWith,    BASE_CHART, 'XUAT_HANH', BASE_RULE, BASE_FILTER).score;
  const scoreWithout = computeScore(dayWithout, BASE_CHART, 'XUAT_HANH', BASE_RULE, BASE_FILTER).score;
  assertEqual(scoreWith, scoreWithout, 'Thiên Xá should have no effect on XUAT_HANH');
});

test('R2f: All THIEN_XA_BONUS_INTENTS give +8, all THIEN_XA_PENALTY_INTENTS give -15', () => {
  const baseScore = computeScore(BASE_DAY, BASE_CHART, 'MAC_DINH', BASE_RULE, BASE_FILTER).score;
  const dayWith = { ...BASE_DAY, hasThienXa: true };

  for (const intent of THIEN_XA_BONUS_INTENTS) {
    const s = computeScore(dayWith, BASE_CHART, intent, BASE_RULE, BASE_FILTER).score;
    const baseForIntent = computeScore(BASE_DAY, BASE_CHART, intent, BASE_RULE, BASE_FILTER).score;
    assertEqual(s, baseForIntent + 8, `${intent}: expected +8, got diff=${s - baseForIntent}`);
  }

  for (const intent of THIEN_XA_PENALTY_INTENTS) {
    const s = computeScore(dayWith, BASE_CHART, intent, BASE_RULE, BASE_FILTER).score;
    const baseForIntent = computeScore(BASE_DAY, BASE_CHART, intent, BASE_RULE, BASE_FILTER).score;
    assertEqual(s, baseForIntent - 15, `${intent}: expected -15, got diff=${s - baseForIntent}`);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// SPECIAL RULE 3 TESTS — Tháng Cô Hồn (filter.js)
// ─────────────────────────────────────────────────────────────────────────────

console.log('\n── Special Rule 3: Tháng Cô Hồn ──────────────────────────────────────────');

test('R3a: DAM_CUOI is blocked in Cô Hồn (tháng 7)', () => {
  const cohonDay = { ...BASE_DAY, lunarMonth: 7, isCohon: true };
  const result = applyLayer2Filter(cohonDay, BASE_CHART, 'DAM_CUOI');
  assert(!result.pass, 'DAM_CUOI should fail in tháng 7');
  assertEqual(result.severity, 3, 'severity should be 3');
  assert(result.reasons[0].includes('Cô Hồn'), 'reason should mention Cô Hồn');
});

test('R3b: DONG_THO is blocked in Cô Hồn', () => {
  const cohonDay = { ...BASE_DAY, lunarMonth: 7, isCohon: true };
  const result = applyLayer2Filter(cohonDay, BASE_CHART, 'DONG_THO');
  assert(!result.pass, 'DONG_THO should fail in tháng 7');
});

test('R3c: NHAP_TRACH is blocked in Cô Hồn', () => {
  const cohonDay = { ...BASE_DAY, lunarMonth: 7, isCohon: true };
  const result = applyLayer2Filter(cohonDay, BASE_CHART, 'NHAP_TRACH');
  assert(!result.pass, 'NHAP_TRACH should fail in tháng 7');
});

test('R3d: KHAI_TRUONG is blocked in Cô Hồn', () => {
  const cohonDay = { ...BASE_DAY, lunarMonth: 7, isCohon: true };
  const result = applyLayer2Filter(cohonDay, BASE_CHART, 'KHAI_TRUONG');
  assert(!result.pass, 'KHAI_TRUONG should fail in tháng 7');
});

test('R3e: XUAT_HANH is NOT blocked in Cô Hồn (not in blocklist)', () => {
  const cohonDay = { ...BASE_DAY, lunarMonth: 7, isCohon: true };
  const result = applyLayer2Filter(cohonDay, BASE_CHART, 'XUAT_HANH');
  assert(result.pass, 'XUAT_HANH should still pass in tháng 7');
});

test('R3f: TE_TU is NOT blocked in Cô Hồn', () => {
  const cohonDay = { ...BASE_DAY, lunarMonth: 7, isCohon: true };
  const result = applyLayer2Filter(cohonDay, BASE_CHART, 'TE_TU');
  assert(result.pass, 'TE_TU should still pass in tháng 7 (cúng bái là bình thường)');
});

test('R3g: Cô Hồn rule checked before personal Xung rule', () => {
  // Day that would also trigger Xung
  const cohonXungDay = {
    ...BASE_DAY,
    lunarMonth: 7,
    isCohon   : true,
    dayChiIdx : 0,  // Tý — xung with Ngọ (chiIdx 6): |0-6|=6 ✓
  };
  const result = applyLayer2Filter(cohonXungDay, BASE_CHART, 'DAM_CUOI');
  assert(!result.pass, 'Should fail');
  assert(result.reasons[0].includes('Cô Hồn'), 'Cô Hồn reason should appear first');
});

// ─────────────────────────────────────────────────────────────────────────────
// COVERAGE CHECK — all 3 rules are non-overlapping
// ─────────────────────────────────────────────────────────────────────────────

console.log('\n── Coverage: COHON_BLOCKED_INTENTS ────────────────────────────────────────');

test('COHON_BLOCKED_INTENTS contains expected 7 intents', () => {
  assertEqual(COHON_BLOCKED_INTENTS.size, 7, `size=${COHON_BLOCKED_INTENTS.size}`);
});

test('THIEN_XA_BONUS_INTENTS and PENALTY sets do not overlap', () => {
  for (const intent of THIEN_XA_BONUS_INTENTS) {
    assert(
      !THIEN_XA_PENALTY_INTENTS.has(intent),
      `${intent} is in both bonus and penalty sets — conflict!`
    );
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// SUMMARY
// ─────────────────────────────────────────────────────────────────────────────

console.log(`\n${'─'.repeat(60)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.log('⚠️  Fix failures before shipping.');
  process.exit(1);
} else {
  console.log('✅  All special rules verified.');
}
