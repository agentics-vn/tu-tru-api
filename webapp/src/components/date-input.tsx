"use client";

import { isValidDate } from "@/lib/utils";

interface DateInputProps {
  day: string;
  month: string;
  year: string;
  onDayChange: (v: string) => void;
  onMonthChange: (v: string) => void;
  onYearChange: (v: string) => void;
  error?: string;
}

export function DateInput({
  day,
  month,
  year,
  onDayChange,
  onMonthChange,
  onYearChange,
  error,
}: DateInputProps) {
  const inputClass =
    "flex-1 bg-transparent border-b border-border py-3 text-center text-lg font-bold focus:outline-none focus:border-fg transition-colors placeholder:text-border focus-visible:ring-1 focus-visible:ring-accent";

  return (
    <div>
      <div className="flex gap-3">
        <input
          type="text"
          inputMode="numeric"
          maxLength={2}
          placeholder="DD"
          value={day}
          onChange={(e) => onDayChange(e.target.value.replace(/\D/g, ""))}
          aria-label="Ngay sinh (ngay)"
          className={`${inputClass} ${error ? "border-bad" : ""}`}
        />
        <span className="text-border self-end pb-3" aria-hidden="true">
          /
        </span>
        <input
          type="text"
          inputMode="numeric"
          maxLength={2}
          placeholder="MM"
          value={month}
          onChange={(e) => onMonthChange(e.target.value.replace(/\D/g, ""))}
          aria-label="Ngay sinh (thang)"
          className={`${inputClass} ${error ? "border-bad" : ""}`}
        />
        <span className="text-border self-end pb-3" aria-hidden="true">
          /
        </span>
        <input
          type="text"
          inputMode="numeric"
          maxLength={4}
          placeholder="YYYY"
          value={year}
          onChange={(e) => onYearChange(e.target.value.replace(/\D/g, ""))}
          aria-label="Ngay sinh (nam)"
          className={`${inputClass} flex-[1.5] ${error ? "border-bad" : ""}`}
        />
      </div>
      {error && (
        <p className="mono-label text-bad mt-2" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export function validateDateInput(
  day: string,
  month: string,
  year: string
): string | null {
  const d = parseInt(day);
  const m = parseInt(month);
  const y = parseInt(year);
  if (!day || !month || !year) return "Vui long nhap day du ngay sinh.";
  if (isNaN(d) || isNaN(m) || isNaN(y)) return "Ngay sinh khong hop le.";
  if (!isValidDate(d, m, y)) return "Ngay sinh khong hop le.";
  return null;
}
