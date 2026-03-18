import type { DayInfo } from "@/lib/mock-data";
import { ScoreBadge } from "./score-badge";

interface DayCardProps {
  day: DayInfo;
  rank?: number;
  expanded?: boolean;
  onToggle?: () => void;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const weekdays = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
  return `${weekdays[d.getDay()]}, ${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}

export function DayCard({
  day,
  rank,
  expanded = false,
  onToggle,
}: DayCardProps) {
  return (
    <div
      className="border-t border-border py-5 cursor-pointer"
      onClick={onToggle}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          {rank && (
            <span className="mono-label text-accent mr-2">
              #{String(rank).padStart(2, "0")}
            </span>
          )}
          <span className="font-bold text-sm">{formatDate(day.date)}</span>
          <div className="mono-label mt-1">
            {day.canChi} — {day.lunarDate} (am lich)
          </div>
        </div>
        <ScoreBadge score={day.score} grade={day.grade} size="sm" />
      </div>

      {/* Score bar */}
      <div className="score-bar mb-3">
        <div
          className="score-bar-fill"
          style={{ width: `${day.score}%` }}
        />
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mb-2">
        <span
          className={`mono-label px-1.5 py-0.5 ${day.hoangDao ? "bg-accent text-bg" : "bg-bg-card"}`}
        >
          {day.hoangDao ? "Hoang dao" : "Hac dao"}
        </span>
        <span className="mono-label px-1.5 py-0.5 bg-bg-card">
          Truc {day.trucName}
        </span>
        <span className="mono-label px-1.5 py-0.5 bg-bg-card">
          {day.sao28} ({day.saoElement})
        </span>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-4 space-y-4 page-enter">
          {/* Good/Bad */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="mono-label text-good mb-2">Nen lam</div>
              {day.goodFor.map((g) => (
                <div key={g} className="text-xs mb-1">
                  {g}
                </div>
              ))}
            </div>
            <div>
              <div className="mono-label text-bad mb-2">Nen tranh</div>
              {day.badFor.map((b) => (
                <div key={b} className="text-xs mb-1">
                  {b}
                </div>
              ))}
            </div>
          </div>

          {/* Hours */}
          <div>
            <div className="mono-label mb-2">Gio tot</div>
            <div className="flex flex-wrap gap-2">
              {day.goodHours.map((h) => (
                <span
                  key={h}
                  className="mono-label px-2 py-1 bg-good/10 text-good"
                >
                  {h}
                </span>
              ))}
              {day.badHours.map((h) => (
                <span
                  key={h}
                  className="mono-label px-2 py-1 bg-bad/10 text-bad"
                >
                  {h}
                </span>
              ))}
            </div>
          </div>

          {/* Reason */}
          <p className="text-xs leading-relaxed text-fg-muted italic">
            &ldquo;{day.reason}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
}
