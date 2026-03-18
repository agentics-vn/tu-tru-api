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

// --- Hop Tuoi (Compatibility) ---

export interface HopTuoiResult {
  person1: { birthDate: string; menh: string; nhatChu: string; hanh: string };
  person2: { birthDate: string; menh: string; nhatChu: string; hanh: string };
  overallScore: number;
  grade: "A" | "B" | "C" | "D";
  nguHanhRelation: string; // "tuong sinh" | "tuong khac" | "binh hoa"
  details: {
    category: string;
    score: number;
    description: string;
  }[];
  summary: string;
  advice: string;
}

export function mockHopTuoiResult(
  date1: string,
  date2: string
): HopTuoiResult {
  const score = 60 + Math.floor(Math.random() * 35);
  return {
    person1: {
      birthDate: date1,
      menh: "Lo Bang Tho",
      nhatChu: "Canh Kim",
      hanh: "Kim",
    },
    person2: {
      birthDate: date2,
      menh: "Dai Lam Moc",
      nhatChu: "Mau Tho",
      hanh: "Moc",
    },
    overallScore: score,
    grade: score >= 85 ? "A" : score >= 70 ? "B" : score >= 50 ? "C" : "D",
    nguHanhRelation: score >= 70 ? "Tuong Sinh" : "Tuong Khac",
    details: [
      {
        category: "Ngu Hanh Nap Am",
        score: 60 + Math.floor(Math.random() * 35),
        description:
          "Kim sinh Thuy, Thuy sinh Moc — vong tuong sinh thuan chieu.",
      },
      {
        category: "Thien Can",
        score: 50 + Math.floor(Math.random() * 40),
        description: "Canh Kim va Mau Tho — Tho sinh Kim, tuong sinh.",
      },
      {
        category: "Dia Chi",
        score: 55 + Math.floor(Math.random() * 35),
        description: "Ngo va Thin — khong xung khong hop, binh hoa.",
      },
      {
        category: "Nhat Chu tuong tac",
        score: 65 + Math.floor(Math.random() * 30),
        description:
          "Hai nhat chu khong xung dot — moi quan he on dinh.",
      },
    ],
    summary:
      "Hai la so co moi quan he Tuong Sinh, ngu hanh ho tro lan nhau. Tho sinh Kim la cuc tot — ben vung va on dinh.",
    advice:
      "Nen chon ngay co hanh Tho hoac Kim de to chuc le cuoi se tang them phuc khi cho ca hai.",
  };
}

// --- Phong Thuy ---

export interface PhongThuyResult {
  dungThan: string;
  kyThan: string;
  huongTot: { direction: string; element: string; reason: string }[];
  huongXau: { direction: string; element: string; reason: string }[];
  mauMayMan: { color: string; hex: string; element: string }[];
  mauKy: { color: string; hex: string; element: string }[];
  soMayMan: number[];
  soKy: number[];
  vatPham: { item: string; element: string; reason: string }[];
}

export function mockPhongThuyResult(): PhongThuyResult {
  return {
    dungThan: "Moc",
    kyThan: "Tho",
    huongTot: [
      {
        direction: "Dong",
        element: "Moc",
        reason: "Chinh Dong thuoc Moc — dung than cua ban.",
      },
      {
        direction: "Dong Nam",
        element: "Moc",
        reason: "Dong Nam thuoc Moc — ho tro su nghiep.",
      },
      {
        direction: "Bac",
        element: "Thuy",
        reason: "Thuy sinh Moc — gian tiep ho tro dung than.",
      },
    ],
    huongXau: [
      {
        direction: "Trung Tam",
        element: "Tho",
        reason: "Tho la ky than — tranh dat ban lam viec o giua nha.",
      },
      {
        direction: "Tay Nam",
        element: "Tho",
        reason: "Tay Nam thuoc Tho — khong nen ngu huong nay.",
      },
    ],
    mauMayMan: [
      { color: "Xanh la", hex: "#3A6B35", element: "Moc" },
      { color: "Xanh duong", hex: "#2B6CB0", element: "Thuy" },
      { color: "Den", hex: "#1A1A1A", element: "Thuy" },
    ],
    mauKy: [
      { color: "Vang dat", hex: "#B8860B", element: "Tho" },
      { color: "Nau", hex: "#8B6914", element: "Tho" },
    ],
    soMayMan: [1, 2, 6],
    soKy: [5, 0],
    vatPham: [
      {
        item: "Cay xanh de ban",
        element: "Moc",
        reason: "Tang cuong Moc khi — tot cho tai loc va suc khoe.",
      },
      {
        item: "Be ca nho",
        element: "Thuy",
        reason: "Thuy sinh Moc — kich hoat dong tien luu thong.",
      },
      {
        item: "Tranh phong canh rung",
        element: "Moc",
        reason: "Tang Moc khi trong khong gian lam viec.",
      },
    ],
  };
}

// --- Su Kien (Events) ---

export interface SavedEvent {
  id: string;
  title: string;
  date: string;
  intent: string;
  note?: string;
  score?: number;
  grade?: "A" | "B" | "C" | "D";
  goodHours?: string[];
}

export function mockSavedEvents(): SavedEvent[] {
  return [
    {
      id: "1",
      title: "Khai truong quan cafe",
      date: "2026-04-15",
      intent: "Khai Truong",
      note: "Dia chi: 123 Nguyen Hue, Q1",
      score: 92,
      grade: "A",
      goodHours: ["7h-9h", "11h-13h"],
    },
    {
      id: "2",
      title: "Le dinh hon",
      date: "2026-05-22",
      intent: "Cuoi Hoi",
      score: 87,
      grade: "B",
      goodHours: ["7h-9h", "9h-11h"],
    },
    {
      id: "3",
      title: "Ky hop dong thue mat bang",
      date: "2026-04-10",
      intent: "Ky Hop Dong",
      score: 85,
      grade: "B",
      goodHours: ["11h-13h"],
    },
  ];
}

// --- So Sanh Ngay (Compare 2 Days) ---

export function mockDayDetail(dateStr: string): DayInfo {
  const d = new Date(dateStr);
  const score = 55 + Math.floor(Math.random() * 40);
  return {
    date: dateStr,
    lunarDate: `${d.getDate()} thang ${d.getMonth() + 1}`,
    canChi: `${pick(CAN)} ${pick(CHI)}`,
    hoangDao: Math.random() > 0.4,
    trucName: pick(TRUC),
    trucScore: Math.random() > 0.5 ? 2 : -1,
    sao28: pick(SAO28),
    saoElement: pick(["Kim", "Moc", "Thuy", "Hoa", "Tho"]),
    score,
    grade: score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : "D",
    goodFor: [pick(INTENTS), pick(INTENTS)],
    badFor: [pick(INTENTS)],
    goodHours: ["7h-9h", "11h-13h", "15h-17h"].slice(
      0,
      1 + Math.floor(Math.random() * 3)
    ),
    badHours: ["9h-11h", "13h-15h"].slice(
      0,
      1 + Math.floor(Math.random() * 2)
    ),
    reason: `Ngay ${pick(["Hoang Dao", "Hac Dao"])} — truc ${pick(TRUC)} ket hop sao ${pick(SAO28)}.`,
    hungNgay: Math.random() > 0.7 ? [pick(["Nguyet Ky", "Tam Nuong", "Tu Ly"])] : [],
  };
}
