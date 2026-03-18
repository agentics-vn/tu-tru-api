"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { mockMonthOverview } from "@/lib/mock-data";

const WEEKDAY_LABELS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

const BADGE_STYLES = {
  good: "bg-good text-bg",
  neutral: "bg-transparent text-fg",
  bad: "bg-bad/15 text-bad",
};

export default function LichPage() {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();
  const now = new Date();
  const [viewYear, setViewYear] = useState(now.getFullYear());
  const [viewMonth, setViewMonth] = useState(now.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  const data = useMemo(
    () => mockMonthOverview(viewYear, viewMonth),
    [viewYear, viewMonth]
  );

  if (isLoaded && !profile) {
    router.replace("/");
    return null;
  }
  if (!isLoaded) return null;

  // First day of month (0=Sun), adjust for Monday start
  const firstDayOfWeek = new Date(viewYear, viewMonth - 1, 1).getDay();
  const offset = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;

  const prevMonth = () => {
    if (viewMonth === 1) {
      setViewMonth(12);
      setViewYear(viewYear - 1);
    } else {
      setViewMonth(viewMonth - 1);
    }
    setSelectedDay(null);
  };

  const nextMonth = () => {
    if (viewMonth === 12) {
      setViewMonth(1);
      setViewYear(viewYear + 1);
    } else {
      setViewMonth(viewMonth + 1);
    }
    setSelectedDay(null);
  };

  const selected = selectedDay
    ? data.days.find((d) => d.day === selectedDay)
    : null;

  return (
    <div className="px-6 py-6 page-enter">
      {/* Header */}
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Lich</div>
      </header>

      {/* Month nav */}
      <div className="flex items-center justify-between mb-8">
        <button onClick={prevMonth} className="mono-label p-2">
          &larr;
        </button>
        <h2 className="heading-display text-2xl">
          Thang {viewMonth}/{viewYear}
        </h2>
        <button onClick={nextMonth} className="mono-label p-2">
          &rarr;
        </button>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-0 mb-2">
        {WEEKDAY_LABELS.map((w) => (
          <div key={w} className="mono-label text-center py-1">
            {w}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-0 mb-6">
        {/* Empty cells for offset */}
        {Array.from({ length: offset }).map((_, i) => (
          <div key={`empty-${i}`} className="aspect-square" />
        ))}

        {/* Day cells */}
        {data.days.map((d) => {
          const isToday =
            d.day === now.getDate() &&
            viewMonth === now.getMonth() + 1 &&
            viewYear === now.getFullYear();
          const isSelected = selectedDay === d.day;

          return (
            <button
              key={d.day}
              onClick={() => setSelectedDay(d.day === selectedDay ? null : d.day)}
              className={`
                aspect-square flex flex-col items-center justify-center
                text-sm transition-colors relative
                ${isSelected ? "bg-fg text-bg" : ""}
              `}
            >
              <span
                className={`
                  text-xs font-medium
                  ${isSelected ? "" : isToday ? "font-bold" : ""}
                `}
              >
                {d.day}
              </span>
              {!isSelected && (
                <span
                  className={`
                    w-1.5 h-1.5 mt-0.5
                    ${d.badge === "good" ? "bg-good" : d.badge === "bad" ? "bg-bad" : "bg-border"}
                  `}
                />
              )}
              {isToday && !isSelected && (
                <span className="absolute bottom-0.5 w-3 h-[1px] bg-fg" />
              )}
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-6">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-good" />
          <span className="mono-label">Tot</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-border" />
          <span className="mono-label">Binh thuong</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-bad" />
          <span className="mono-label">Xau</span>
        </div>
      </div>

      {/* Selected day detail */}
      {selected && (
        <div className="border-t border-border pt-5 page-enter">
          <div className="flex items-center justify-between mb-3">
            <span className="font-bold text-sm">
              Ngay {selected.day}/{viewMonth}/{viewYear}
            </span>
            <span
              className={`mono-label px-2 py-0.5 ${BADGE_STYLES[selected.badge]}`}
            >
              {selected.badge === "good"
                ? "Hoang Dao"
                : selected.badge === "bad"
                  ? "Hac Dao"
                  : "Binh thuong"}
            </span>
          </div>
          {selected.summary && (
            <p className="text-xs text-fg-muted leading-relaxed mb-4">
              {selected.summary}
            </p>
          )}
          <button className="btn-outline w-full text-[0.6rem]">
            Xem chi tiet
          </button>
        </div>
      )}
    </div>
  );
}
