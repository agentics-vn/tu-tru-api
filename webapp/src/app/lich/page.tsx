"use client";

import { useState } from "react";
import { useRequireProfile } from "@/lib/use-require-profile";
import { useApi } from "@/lib/use-api";
import { fetchLichThang, type LichThangDay } from "@/lib/api";

const WEEKDAY_LABELS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

export default function LichPage() {
  const { profile, isReady } = useRequireProfile();
  const now = new Date();
  const [viewYear, setViewYear] = useState(now.getFullYear());
  const [viewMonth, setViewMonth] = useState(now.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState<LichThangDay | null>(null);

  const monthStr = `${viewYear}-${String(viewMonth).padStart(2, "0")}`;

  const { data, loading, error } = useApi(
    isReady && profile
      ? () =>
          fetchLichThang({
            birthDate: profile.birthDate,
            birthHour: profile.birthHour,
            gender: profile.gender,
            month: monthStr,
          })
      : null,
    [profile?.birthDate, monthStr]
  );

  if (!isReady) return null;

  const firstDayOfWeek = new Date(viewYear, viewMonth - 1, 1).getDay();
  const offset = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;

  const prevMonth = () => {
    if (viewMonth === 1) { setViewMonth(12); setViewYear(viewYear - 1); }
    else setViewMonth(viewMonth - 1);
    setSelectedDay(null);
  };

  const nextMonth = () => {
    if (viewMonth === 12) { setViewMonth(1); setViewYear(viewYear + 1); }
    else setViewMonth(viewMonth + 1);
    setSelectedDay(null);
  };

  function badgeForDay(d: LichThangDay): "good" | "neutral" | "bad" {
    if (d.is_hoang_dao && d.truc_score >= 1) return "good";
    if (!d.is_hoang_dao && d.truc_score < 0) return "bad";
    return "neutral";
  }

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Lich</div>
      </header>

      <div className="flex items-center justify-between mb-8">
        <button type="button" onClick={prevMonth} className="mono-label p-2" aria-label="Thang truoc">&larr;</button>
        <h2 className="heading-display text-2xl">Thang {viewMonth}/{viewYear}</h2>
        <button type="button" onClick={nextMonth} className="mono-label p-2" aria-label="Thang sau">&rarr;</button>
      </div>

      <div className="grid grid-cols-7 gap-0 mb-2">
        {WEEKDAY_LABELS.map((w) => (
          <div key={w} className="mono-label text-center py-1">{w}</div>
        ))}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="mono-label text-accent">Dang tai...</div>
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center py-20 gap-2">
          <div className="mono-label text-bad">Loi tai du lieu</div>
          <p className="text-xs text-fg-muted">{error}</p>
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-7 gap-0 mb-6" role="grid">
            {Array.from({ length: offset }).map((_, i) => (
              <div key={`empty-${i}`} className="aspect-square" />
            ))}

            {data.days.map((d) => {
              const dayNum = new Date(d.date).getDate();
              const isToday = d.date === now.toISOString().slice(0, 10);
              const isSelected = selectedDay?.date === d.date;
              const badge = badgeForDay(d);

              return (
                <button
                  type="button"
                  key={d.date}
                  onClick={() => setSelectedDay(isSelected ? null : d)}
                  aria-label={`Ngay ${dayNum}, ${badge === "good" ? "tot" : badge === "bad" ? "xau" : "binh thuong"}`}
                  aria-pressed={isSelected}
                  className={`aspect-square flex flex-col items-center justify-center text-sm transition-colors relative ${isSelected ? "bg-fg text-bg" : ""}`}
                >
                  <span className={`text-xs font-medium ${isSelected ? "" : isToday ? "font-bold" : ""}`}>
                    {dayNum}
                  </span>
                  {!isSelected && (
                    <span className={`w-1.5 h-1.5 mt-0.5 ${badge === "good" ? "bg-good" : badge === "bad" ? "bg-bad" : "bg-border"}`} />
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
            <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 bg-good" /><span className="mono-label">Tot</span></div>
            <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 bg-border" /><span className="mono-label">Binh thuong</span></div>
            <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 bg-bad" /><span className="mono-label">Xau</span></div>
          </div>

          {data.user_menh && (
            <div className="mono-label mb-6">
              Menh: {data.user_menh.name} ({data.user_menh.hanh})
            </div>
          )}

          {/* Selected day detail */}
          {selectedDay && (
            <div className="border-t border-border pt-5 page-enter">
              <div className="flex items-center justify-between mb-3">
                <span className="font-bold text-sm">{selectedDay.can_chi_name}</span>
                <span className={`mono-label px-2 py-0.5 ${selectedDay.is_hoang_dao ? "bg-accent text-bg" : "bg-bg-card"}`}>
                  {selectedDay.is_hoang_dao ? `Hoang Dao (${selectedDay.star_name})` : "Hac Dao"}
                </span>
              </div>
              <div className="mono-label mb-2">
                Am lich: {selectedDay.lunar_day}/{selectedDay.lunar_month} — Truc {selectedDay.truc_name}
              </div>
              {selectedDay.sao_28 && (
                <div className="mono-label mb-2">
                  Sao 28 Tu: {selectedDay.sao_28.name} ({selectedDay.sao_28.hanh}) — {selectedDay.sao_28.tot_xau}
                </div>
              )}
              {selectedDay.summary && (
                <div className="mt-3">
                  {selectedDay.summary.tot.length > 0 && (
                    <div className="mb-2">
                      <span className="mono-label text-good">Tot: </span>
                      <span className="text-xs">{selectedDay.summary.tot.join(", ")}</span>
                    </div>
                  )}
                  {selectedDay.summary.xau.length > 0 && (
                    <div className="mb-2">
                      <span className="mono-label text-bad">Xau: </span>
                      <span className="text-xs">{selectedDay.summary.xau.join(", ")}</span>
                    </div>
                  )}
                </div>
              )}
              {selectedDay.gio_hoang_dao && selectedDay.gio_hoang_dao.length > 0 && (
                <div className="mt-3">
                  <div className="mono-label mb-1">Gio Hoang Dao</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedDay.gio_hoang_dao.map((g) => (
                      <span key={g.chi_name} className="mono-label px-2 py-1 bg-good/10 text-good">
                        {g.chi_name} ({g.range})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
