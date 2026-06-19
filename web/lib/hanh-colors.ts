import type { Hanh } from "./types";

export const HANH_CLASS: Record<Hanh, string> = {
  Mộc: "text-hanh-moc",
  Hỏa: "text-hanh-hoa",
  Thổ: "text-hanh-tho",
  Kim: "text-hanh-kim",
  Thủy: "text-hanh-thuy",
};

export const HANH_BG: Record<Hanh, string> = {
  Mộc: "bg-hanh-moc/10",
  Hỏa: "bg-hanh-hoa/10",
  Thổ: "bg-hanh-tho/10",
  Kim: "bg-hanh-kim/10",
  Thủy: "bg-hanh-thuy/10",
};
