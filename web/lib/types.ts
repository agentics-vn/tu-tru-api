export type Hanh = "Kim" | "Mộc" | "Thủy" | "Hỏa" | "Thổ";

export interface LaSoFullRequest {
  birth_date: string;
  birth_time: number;
  gender: number;
  birth_minute?: number;
  name?: string;
  view_year?: number;
}

export interface StarItem {
  key: string;
  name: string;
}

export interface PillarRow {
  key: string;
  display: string;
  can: { name: string; hanh: Hanh };
  chi: { name: string; hanh: Hanh };
  nap_am: { name: string; hanh: Hanh };
  thap_than: { short_label: string; name: string };
  tang_can: { can_name: string; hanh: Hanh }[];
  pho_tinh: { short_label: string }[];
  truong_sinh: { label_vi: string };
  than_sat: StarItem[];
}

export interface MenhBanPayload {
  tu_tru_display: string;
  header: {
    name?: string;
    gender_label: string;
    duong_lich: string;
    duong_lich_display: string;
    am_lich: { display: string };
    tiet_khi: { name: string };
    nguyet_lenh: string;
    khoi_van_date: string;
    birth_time_label?: string;
  };
  pillars: Record<"year" | "month" | "day" | "hour", PillarRow>;
  dai_van: {
    khoi_van_date: string;
    cycles: {
      display: string;
      age_label: string;
      start_year: number;
    }[];
  };
  luu_nien: {
    year: number;
    display: string;
    age_label: string;
    selected?: boolean;
  }[];
  menh_cung: { display: string };
  thai_nguyen: { display: string };
  tuan_khong: {
    nien_khong: { display: string };
    nhat_khong: { display: string };
  };
}

export interface LaSoFullResponse {
  status: string;
  menh_ban: MenhBanPayload;
}
