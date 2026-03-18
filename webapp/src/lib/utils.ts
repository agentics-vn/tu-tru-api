// Shared utility functions

const WEEKDAYS = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${WEEKDAYS[d.getDay()]}, ${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}

export function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr);
  return `${WEEKDAYS[d.getDay()]}, ${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function daysUntil(dateStr: string): number {
  const target = new Date(dateStr);
  const now = new Date();
  const targetDay = new Date(target.getFullYear(), target.getMonth(), target.getDate());
  const nowDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.ceil((targetDay.getTime() - nowDay.getTime()) / (1000 * 60 * 60 * 24));
}

export function isValidDate(day: number, month: number, year: number): boolean {
  if (year < 1920 || year > new Date().getFullYear() - 1) return false;
  if (month < 1 || month > 12) return false;
  if (day < 1) return false;
  const maxDay = new Date(year, month, 0).getDate();
  return day <= maxDay;
}

export const HANH_COLORS: Record<string, string> = {
  Kim: "text-fg",
  Moc: "text-good",
  Thuy: "text-[#2B6CB0]",
  Hoa: "text-bad",
  Tho: "text-warn",
};
