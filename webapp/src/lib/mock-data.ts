// Mock data for UI development — will be replaced with API calls

export interface DayInfo {
  date: string;
  lunarDate: string;
  canChi: string;
  hoangDao: boolean;
  trucName: string;
  trucScore: number;
  sao28: string;
  saoElement: string;
  score: number;
  grade: "A" | "B" | "C" | "D";
  goodFor: string[];
  badFor: string[];
  goodHours: string[];
  badHours: string[];
  reason: string;
  hungNgay: string[];
  severity?: number;
}

export interface TuTruChart {
  gio: { can: string; chi: string; napAm: string; hanh: string };
  ngay: { can: string; chi: string; napAm: string; hanh: string };
  thang: { can: string; chi: string; napAm: string; hanh: string };
  nam: { can: string; chi: string; napAm: string; hanh: string };
  nhatChu: string;
  cuongNhuoc: "vuong" | "nhuoc";
  menh: string;
  dungThan: string;
  kyThan: string;
}

export interface MonthOverview {
  year: number;
  month: number;
  days: {
    date: string;
    day: number;
    badge: "good" | "neutral" | "bad";
    hoangDao: boolean;
    summary?: string;
  }[];
}

export interface ChonNgayResult {
  intent: string;
  range: { from: string; to: string };
  totalDays: number;
  layer1Pass: number;
  layer2Pass: number;
  recommended: DayInfo[];
  avoid: { date: string; reason: string; severity: number }[];
}

// --- Mock generators ---

const CAN = [
  "Giap",
  "At",
  "Binh",
  "Dinh",
  "Mau",
  "Ky",
  "Canh",
  "Tan",
  "Nham",
  "Quy",
];
const CHI = [
  "Ty",
  "Suu",
  "Dan",
  "Mao",
  "Thin",
  "Ty",
  "Ngo",
  "Mui",
  "Than",
  "Dau",
  "Tuat",
  "Hoi",
];
const TRUC = [
  "Kien",
  "Tru",
  "Man",
  "Binh",
  "Dinh",
  "Chap",
  "Pha",
  "Nguy",
  "Thanh",
  "Thu",
  "Khai",
  "Be",
];
const SAO28 = [
  "Giac",
  "Cang",
  "Đe",
  "Phong",
  "Tam",
  "Vi",
  "Co",
  "Dau",
  "Nguu",
  "Nu",
];
const INTENTS = [
  "Khai Truong",
  "Cuoi Hoi",
  "Dong Tho",
  "Nhap Trach",
  "Xuat Hanh",
  "Ky Hop Dong",
  "Te Tu",
  "Kham Benh",
];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function mockTodayInfo(): DayInfo {
  const score = 75 + Math.floor(Math.random() * 20);
  return {
    date: "2026-03-18",
    lunarDate: "29 thang Hai",
    canChi: `${pick(CAN)} ${pick(CHI)}`,
    hoangDao: true,
    trucName: "Thanh",
    trucScore: 2,
    sao28: "Sam",
    saoElement: "Thuy",
    score,
    grade: score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : "D",
    goodFor: ["Khai truong", "Ky hop dong", "Gap doi tac"],
    badFor: ["Phau thuat", "Kien tung"],
    goodHours: ["7h-9h", "11h-13h", "15h-17h"],
    badHours: ["9h-11h", "13h-15h"],
    reason:
      "Ngay Hoang Dao Kim Quy ket hop Dung Than Moc cua ban duoc ho tro — rat thuan loi cho tai loc va ky ket.",
    hungNgay: [],
  };
}

export function mockTuTruChart(): TuTruChart {
  return {
    gio: { can: "Mau", chi: "Thin", napAm: "Dai Lam Moc", hanh: "Moc" },
    ngay: { can: "Canh", chi: "Ngo", napAm: "Lo Bang Tho", hanh: "Tho" },
    thang: { can: "Ky", chi: "Mao", napAm: "Thanh Trung Tho", hanh: "Tho" },
    nam: { can: "Canh", chi: "Ngo", napAm: "Lo Bang Tho", hanh: "Tho" },
    nhatChu: "Canh Kim",
    cuongNhuoc: "vuong",
    menh: "Lo Bang Tho",
    dungThan: "Moc",
    kyThan: "Tho",
  };
}

export function mockMonthOverview(
  year: number,
  month: number
): MonthOverview {
  const daysInMonth = new Date(year, month, 0).getDate();
  const days = [];
  for (let d = 1; d <= daysInMonth; d++) {
    const r = Math.random();
    days.push({
      date: `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
      day: d,
      badge: (r > 0.7 ? "good" : r > 0.2 ? "neutral" : "bad") as
        | "good"
        | "neutral"
        | "bad",
      hoangDao: r > 0.5,
      summary:
        r > 0.7
          ? "Hoang Dao — tot cho khai truong"
          : r < 0.2
            ? "Hac Dao — nen tranh viec lon"
            : undefined,
    });
  }
  return { year, month, days };
}

export function mockChonNgayResult(intent: string): ChonNgayResult {
  const recommended: DayInfo[] = Array.from({ length: 5 }, (_, i) => ({
    date: `2026-04-${String(10 + i * 5).padStart(2, "0")}`,
    lunarDate: `${14 + i} thang Ba`,
    canChi: `${CAN[i]} ${CHI[i]}`,
    hoangDao: true,
    trucName: pick(TRUC),
    trucScore: 2,
    sao28: pick(SAO28),
    saoElement: "Thuy",
    score: 92 - i * 4,
    grade: (i === 0 ? "A" : i < 3 ? "B" : "C") as "A" | "B" | "C" | "D",
    goodFor: [intent, "Gap doi tac"],
    badFor: ["Phau thuat"],
    goodHours: ["7h-9h", "11h-13h"],
    badHours: ["9h-11h"],
    reason: `Ngay Hoang Dao ket hop truc ${pick(TRUC)} — phu hop cho ${intent.toLowerCase()}.`,
    hungNgay: [],
  }));

  return {
    intent,
    range: { from: "2026-04-01", to: "2026-06-30" },
    totalDays: 91,
    layer1Pass: 64,
    layer2Pass: 41,
    recommended,
    avoid: [
      { date: "2026-04-07", reason: "Nguyet Ky", severity: 3 },
      { date: "2026-04-12", reason: "Tam Nuong", severity: 2 },
    ],
  };
}

export const BIRTH_HOURS = [
  { value: "unknown", label: "Khong ro" },
  { value: "ty", label: "Ty (23h-1h)" },
  { value: "suu", label: "Suu (1h-3h)" },
  { value: "dan", label: "Dan (3h-5h)" },
  { value: "mao", label: "Mao (5h-7h)" },
  { value: "thin", label: "Thin (7h-9h)" },
  { value: "ti", label: "Ty (9h-11h)" },
  { value: "ngo", label: "Ngo (11h-13h)" },
  { value: "mui", label: "Mui (13h-15h)" },
  { value: "than", label: "Than (15h-17h)" },
  { value: "dau", label: "Dau (17h-19h)" },
  { value: "tuat", label: "Tuat (19h-21h)" },
  { value: "hoi", label: "Hoi (21h-23h)" },
];

export const INTENT_OPTIONS = INTENTS.map((i) => ({
  value: i.toLowerCase().replace(/\s/g, "-"),
  label: i,
}));
