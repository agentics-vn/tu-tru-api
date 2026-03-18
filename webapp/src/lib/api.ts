/**
 * API client for tu-tru-api.fly.dev
 * All dates sent as dd/mm/yyyy, received as YYYY-MM-DD
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://tu-tru-api.fly.dev";

// --- Types matching API responses ---

export interface ApiMeta {
  intent: string;
  range_scanned: { from: string; to: string };
  total_days_scanned: number;
  days_passed_layer1: number;
  days_passed_layer2: number;
  bat_tu_summary: {
    ngu_hanh_menh: string;
    duong_than: string;
    ky_than: string;
  };
}

export interface RecommendedDate {
  date: string;
  lunar_date: string;
  score: number;
  grade: string;
  truc: string;
  sao_cat: string[];
  sao_hung: string[];
  nguhanh_day: string;
  reason_vi: string;
  summary_vi: string;
  time_slots: string[];
}

export interface AvoidDate {
  date: string;
  reason_vi: string;
  severity: number;
}

export interface ChonNgayResponse {
  status: string;
  meta: ApiMeta;
  recommended_dates: RecommendedDate[];
  dates_to_avoid: AvoidDate[];
}

export interface LichThangDay {
  date: string;
  lunar_day: number;
  lunar_month: number;
  can_chi_name: string;
  is_hoang_dao: boolean;
  star_name: string;
  badge: string;
  truc_name: string;
  truc_score: number;
  is_layer1_pass: boolean;
  gio_hoang_dao?: { chi_name: string; range: string }[];
  sao_28?: { name: string; hanh: string; tot_xau: string };
  summary?: { tot: string[]; xau: string[]; rating: string };
}

export interface LichThangResponse {
  status: string;
  month: string;
  user_menh: { hanh: string; name: string };
  days: LichThangDay[];
}

export interface PillarInfo {
  can_chi: string;
  can: { idx: number; name: string };
  chi: { idx: number; name: string };
  nap_am: { hanh: string; name: string };
}

export interface TuTruResponse {
  status: string;
  birth_date: string;
  birth_time?: number;
  birth_time_label?: string;
  birth_year_can_chi: string;
  menh: {
    nap_am_name: string;
    hanh: string;
    duong_than: string;
    ky_than: string;
  };
  tu_tru_display?: string;
  pillars?: {
    year: PillarInfo;
    month: PillarInfo;
    day: PillarInfo;
    hour: PillarInfo;
  };
  nhat_chu?: { can_name: string; hanh: string };
  chart_strength?: string;
  dung_than?: { element: string; description: string };
  hi_than?: { element: string; description: string };
  ky_than?: { element: string; description: string };
  cuu_than?: { element: string; description: string };
  thap_than?: {
    year?: { key: string; name: string; category: string };
    month?: { key: string; name: string; category: string };
    hour?: { key: string; name: string; category: string };
    dominant?: { key: string; name: string };
  };
  gender?: number;
  dai_van?: {
    direction: string;
    current: {
      display: string;
      hanh: string;
      nap_am_hanh: string;
      age_range: string;
    };
    cycles: {
      cycle_num: number;
      display: string;
      hanh: string;
      nap_am_hanh: string;
      age_range: string;
    }[];
  };
  _note?: string;
}

export interface NgayHomNayResponse {
  status: string;
  date: string;
  can_chi: {
    name: string;
    can_name: string;
    chi_name: string;
    nap_am_hanh: string;
  };
  lunar: {
    day: number;
    month: number;
    year: number;
    display: string;
  };
  hoang_dao: {
    is_hoang_dao: boolean;
    star_name: string;
    badge: string;
  };
  truc: { name: string; score: number };
  good_for: string[];
  avoid_for: string[];
  gio_tot: { chi_name: string; range: string }[];
  gio_xau: { chi_name: string; range: string }[];
  daily_advice: { nen_lam: string; nen_tranh: string };
  bat_tu?: TuTruResponse;
}

export interface TieuVanResponse {
  status: string;
  month: string;
  tieu_van_pillar: {
    can_name: string;
    chi_name: string;
    display: string;
    nap_am_hanh: string;
    nap_am_name: string;
  };
  user_menh: { hanh: string; name: string };
  element_relation: string;
  reading: string;
  tags: string[];
  nhat_chu?: { can_name: string; hanh: string };
  dung_than?: { element: string };
  chart_strength?: string;
  dai_van_context?: unknown;
}

// --- Helper: convert YYYY-MM-DD to dd/mm/yyyy ---
export function toDmy(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

// --- Birth time mapping ---
// Profile stores: "ty","suu","dan","mao","thin","ti","ngo","mui","than","dau","tuat","hoi","unknown"
// API expects integer hours
const HOUR_MAP: Record<string, number | undefined> = {
  ty: 0,
  suu: 2,
  dan: 4,
  mao: 6,
  thin: 8,
  ti: 10,
  ngo: 11,
  mui: 14,
  than: 16,
  dau: 18,
  tuat: 20,
  hoi: 22,
  unknown: undefined,
};

export function birthHourToApi(hourKey: string): number | undefined {
  return HOUR_MAP[hourKey];
}

// --- Fetch wrapper ---
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      res.status,
      body.error_code || "UNKNOWN",
      body.message || `API returned ${res.status}`
    );
  }

  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// --- API functions ---

export async function fetchNgayHomNay(params: {
  birthDate: string; // YYYY-MM-DD
  birthHour?: string;
  gender?: "nam" | "nu";
  date?: string; // YYYY-MM-DD
}): Promise<NgayHomNayResponse> {
  const query = new URLSearchParams();
  query.set("birth_date", toDmy(params.birthDate));
  const bt = params.birthHour ? birthHourToApi(params.birthHour) : undefined;
  if (bt !== undefined) query.set("birth_time", String(bt));
  if (params.gender) query.set("gender", params.gender === "nam" ? "1" : "-1");
  if (params.date) query.set("date", params.date);

  return apiFetch<NgayHomNayResponse>(`/v1/ngay-hom-nay?${query}`);
}

export async function fetchLichThang(params: {
  birthDate: string;
  birthHour?: string;
  gender?: "nam" | "nu";
  month: string; // YYYY-MM
}): Promise<LichThangResponse> {
  const query = new URLSearchParams();
  query.set("birth_date", toDmy(params.birthDate));
  const bt = params.birthHour ? birthHourToApi(params.birthHour) : undefined;
  if (bt !== undefined) query.set("birth_time", String(bt));
  if (params.gender) query.set("gender", params.gender === "nam" ? "1" : "-1");
  query.set("month", params.month);

  return apiFetch<LichThangResponse>(`/v1/lich-thang?${query}`);
}

export async function fetchChonNgay(params: {
  birthDate: string;
  birthHour?: string;
  gender?: "nam" | "nu";
  intent: string;
  rangeStart: string; // YYYY-MM-DD
  rangeEnd: string;
  topN?: number;
}): Promise<ChonNgayResponse> {
  const bt = params.birthHour ? birthHourToApi(params.birthHour) : undefined;
  return apiFetch<ChonNgayResponse>("/v1/chon-ngay", {
    method: "POST",
    body: JSON.stringify({
      birth_date: toDmy(params.birthDate),
      birth_time: bt,
      gender: params.gender === "nam" ? 1 : params.gender === "nu" ? -1 : undefined,
      intent: params.intent,
      range_start: toDmy(params.rangeStart),
      range_end: toDmy(params.rangeEnd),
      top_n: params.topN || 3,
    }),
  });
}

export async function fetchTuTru(params: {
  birthDate: string;
  birthHour?: string;
  gender?: "nam" | "nu";
}): Promise<TuTruResponse> {
  const bt = params.birthHour ? birthHourToApi(params.birthHour) : undefined;
  return apiFetch<TuTruResponse>("/v1/tu-tru", {
    method: "POST",
    body: JSON.stringify({
      birth_date: toDmy(params.birthDate),
      birth_time: bt,
      gender: params.gender === "nam" ? 1 : params.gender === "nu" ? -1 : undefined,
    }),
  });
}

export async function fetchTieuVan(params: {
  birthDate: string;
  birthHour?: string;
  gender?: "nam" | "nu";
  month: string; // YYYY-MM
}): Promise<TieuVanResponse> {
  const query = new URLSearchParams();
  query.set("birth_date", toDmy(params.birthDate));
  const bt = params.birthHour ? birthHourToApi(params.birthHour) : undefined;
  if (bt !== undefined) query.set("birth_time", String(bt));
  if (params.gender) query.set("gender", params.gender === "nam" ? "1" : "-1");
  query.set("month", params.month);

  return apiFetch<TieuVanResponse>(`/v1/tieu-van?${query}`);
}

// --- Hop Tuoi (Compatibility) ---

export interface HopTuoiResponse {
  status: string;
  person1: { birth_date: string; menh: string; hanh: string; nhatChu: string };
  person2: { birth_date: string; menh: string; hanh: string; nhatChu: string };
  overall_score: number;
  grade: string;
  ngu_hanh_relation: string;
  details: { category: string; score: number; description: string }[];
  summary: string;
  advice: string;
}

export async function fetchHopTuoi(params: {
  person1BirthDate: string;
  person1BirthHour?: string;
  person1Gender?: "nam" | "nu";
  person2BirthDate: string;
  person2BirthHour?: string;
  person2Gender?: "nam" | "nu";
}): Promise<HopTuoiResponse> {
  const bt1 = params.person1BirthHour ? birthHourToApi(params.person1BirthHour) : undefined;
  const bt2 = params.person2BirthHour ? birthHourToApi(params.person2BirthHour) : undefined;
  return apiFetch<HopTuoiResponse>("/v1/hop-tuoi", {
    method: "POST",
    body: JSON.stringify({
      person1_birth_date: toDmy(params.person1BirthDate),
      person1_birth_time: bt1,
      person1_gender: params.person1Gender === "nam" ? 1 : params.person1Gender === "nu" ? -1 : undefined,
      person2_birth_date: toDmy(params.person2BirthDate),
      person2_birth_time: bt2,
      person2_gender: params.person2Gender === "nam" ? 1 : params.person2Gender === "nu" ? -1 : undefined,
    }),
  });
}

// --- Phong Thuy ---

export interface PhongThuyResponse {
  status: string;
  user_menh: { hanh: string; name: string };
  dung_than: string;
  ky_than: string;
  huong_tot: { direction: string; element: string; reason: string }[];
  huong_xau: { direction: string; element: string; reason: string }[];
  mau_may_man: { color: string; hex: string; element: string }[];
  mau_ky: { color: string; hex: string; element: string }[];
  so_may_man: number[];
  so_ky: number[];
  vat_pham: { item: string; element: string; reason: string }[];
}

export async function fetchPhongThuy(params: {
  birthDate: string;
  birthHour?: string;
  gender?: "nam" | "nu";
}): Promise<PhongThuyResponse> {
  const query = new URLSearchParams();
  query.set("birth_date", toDmy(params.birthDate));
  const bt = params.birthHour ? birthHourToApi(params.birthHour) : undefined;
  if (bt !== undefined) query.set("birth_time", String(bt));
  if (params.gender) query.set("gender", params.gender === "nam" ? "1" : "-1");

  return apiFetch<PhongThuyResponse>(`/v1/phong-thuy?${query}`);
}

// --- Day Detail (for So Sanh) ---

export interface DayDetailResponse {
  status: string;
  date: string;
  lunar_date: string;
  can_chi: string;
  hoang_dao: boolean;
  star_name: string;
  truc_name: string;
  truc_score: number;
  sao_28: string;
  sao_element: string;
  score: number;
  grade: string;
  good_for: string[];
  bad_for: string[];
  good_hours: string[];
  bad_hours: string[];
  reason: string;
  hung_ngay: string[];
}

export async function fetchDayDetail(params: {
  birthDate: string;
  birthHour?: string;
  gender?: "nam" | "nu";
  date: string; // YYYY-MM-DD
}): Promise<DayDetailResponse> {
  const query = new URLSearchParams();
  query.set("birth_date", toDmy(params.birthDate));
  const bt = params.birthHour ? birthHourToApi(params.birthHour) : undefined;
  if (bt !== undefined) query.set("birth_time", String(bt));
  if (params.gender) query.set("gender", params.gender === "nam" ? "1" : "-1");
  query.set("date", params.date);

  return apiFetch<DayDetailResponse>(`/v1/day-detail?${query}`);
}
