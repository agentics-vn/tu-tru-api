"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { mockDayDetail } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";
import { ScoreBadge } from "@/components/score-badge";

export default function SoSanhPage() {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();

  const [date1, setDate1] = useState("");
  const [date2, setDate2] = useState("");
  const [comparing, setComparing] = useState(false);

  const day1 = useMemo(
    () => (comparing && date1 ? mockDayDetail(date1) : null),
    [comparing, date1]
  );
  const day2 = useMemo(
    () => (comparing && date2 ? mockDayDetail(date2) : null),
    [comparing, date2]
  );

  if (isLoaded && !profile) {
    router.replace("/");
    return null;
  }
  if (!isLoaded) return null;

  const handleCompare = () => {
    if (date1 && date2) setComparing(true);
  };

  function formatDate(d: string) {
    const dt = new Date(d);
    const wd = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
    return `${wd[dt.getDay()]}, ${String(dt.getDate()).padStart(2, "0")}/${String(dt.getMonth() + 1).padStart(2, "0")}`;
  }

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">So sanh</div>
      </header>

      <div className="flex items-start justify-between mb-10">
        <div>
          <h1 className="heading-display text-[2rem] leading-tight">
            So sanh
            <br />
            hai ngay
          </h1>
          <p className="text-xs text-fg-muted mt-2 max-w-[220px] leading-relaxed">
            Dang phan van giua 2 ngay? So sanh chi tiet de chon ngay phu hop nhat.
          </p>
        </div>
        <BracketText className="mt-1">
          <div className="flex flex-col items-center text-base">
            <span>so</span>
            <span>sanh</span>
          </div>
        </BracketText>
      </div>

      {/* Date inputs */}
      {!comparing && (
        <div className="space-y-6">
          <div>
            <label className="mono-label block mb-3">Ngay thu nhat</label>
            <input
              type="date"
              value={date1}
              onChange={(e) => setDate1(e.target.value)}
              className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
            />
          </div>
          <div>
            <label className="mono-label block mb-3">Ngay thu hai</label>
            <input
              type="date"
              value={date2}
              onChange={(e) => setDate2(e.target.value)}
              className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
            />
          </div>
          <button
            onClick={handleCompare}
            className={`btn-primary w-full ${!date1 || !date2 ? "opacity-30 cursor-not-allowed" : ""}`}
            disabled={!date1 || !date2}
          >
            So sanh
          </button>
        </div>
      )}

      {/* Comparison result */}
      {comparing && day1 && day2 && (
        <div className="page-enter">
          <button
            onClick={() => setComparing(false)}
            className="mono-label mb-6 flex items-center gap-1"
          >
            &larr; Chon lai
          </button>

          {/* Side-by-side header */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className={`text-center p-3 ${day1.score >= day2.score ? "border border-accent" : "border border-border"}`}>
              <div className="text-sm font-bold">{formatDate(date1)}</div>
              <div className="mono-label">{day1.canChi}</div>
            </div>
            <div className={`text-center p-3 ${day2.score >= day1.score ? "border border-accent" : "border border-border"}`}>
              <div className="text-sm font-bold">{formatDate(date2)}</div>
              <div className="mono-label">{day2.canChi}</div>
            </div>
          </div>

          {/* Score comparison */}
          <div className="border-t border-b border-border py-5 mb-6">
            <div className="mono-label mb-3 text-center">Diem tong</div>
            <div className="grid grid-cols-2 gap-3 text-center">
              <div>
                <ScoreBadge score={day1.score} grade={day1.grade} size="md" />
              </div>
              <div>
                <ScoreBadge score={day2.score} grade={day2.grade} size="md" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${day1.score}%` }} />
              </div>
              <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${day2.score}%` }} />
              </div>
            </div>
          </div>

          {/* Attribute rows */}
          {[
            {
              label: "Hoang Dao",
              v1: day1.hoangDao ? "Co" : "Khong",
              v2: day2.hoangDao ? "Co" : "Khong",
              w1: day1.hoangDao,
              w2: day2.hoangDao,
            },
            {
              label: "Truc",
              v1: day1.trucName,
              v2: day2.trucName,
              w1: day1.trucScore > 0,
              w2: day2.trucScore > 0,
            },
            {
              label: "Sao 28 Tu",
              v1: `${day1.sao28} (${day1.saoElement})`,
              v2: `${day2.sao28} (${day2.saoElement})`,
              w1: true,
              w2: true,
            },
            {
              label: "Hung ngay",
              v1: day1.hungNgay.length === 0 ? "Khong" : day1.hungNgay.join(", "),
              v2: day2.hungNgay.length === 0 ? "Khong" : day2.hungNgay.join(", "),
              w1: day1.hungNgay.length === 0,
              w2: day2.hungNgay.length === 0,
            },
          ].map((row) => (
            <div key={row.label} className="grid grid-cols-[1fr_auto_1fr] gap-2 mb-3 items-center">
              <div className={`text-xs text-center p-2 ${row.w1 && !row.w2 ? "bg-good/10" : ""}`}>
                {row.v1}
              </div>
              <div className="mono-label text-center min-w-[70px]">{row.label}</div>
              <div className={`text-xs text-center p-2 ${row.w2 && !row.w1 ? "bg-good/10" : ""}`}>
                {row.v2}
              </div>
            </div>
          ))}

          {/* Good for */}
          <div className="border-t border-border pt-5 mt-4 mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="mono-label text-good mb-2">Nen lam</div>
                {day1.goodFor.map((g) => (
                  <div key={g} className="text-xs mb-1">{g}</div>
                ))}
              </div>
              <div>
                <div className="mono-label text-good mb-2">Nen lam</div>
                {day2.goodFor.map((g) => (
                  <div key={g} className="text-xs mb-1">{g}</div>
                ))}
              </div>
            </div>
          </div>

          {/* Hours */}
          <div className="border-t border-border pt-5 mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="mono-label mb-2">Gio tot</div>
                <div className="flex flex-wrap gap-1">
                  {day1.goodHours.map((h) => (
                    <span key={h} className="mono-label px-2 py-1 bg-good/10 text-good">
                      {h}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <div className="mono-label mb-2">Gio tot</div>
                <div className="flex flex-wrap gap-1">
                  {day2.goodHours.map((h) => (
                    <span key={h} className="mono-label px-2 py-1 bg-good/10 text-good">
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Verdict */}
          <div className="bg-bg-card p-4 mb-6">
            <div className="mono-label text-accent mb-2">Ket luan</div>
            <p className="text-xs leading-relaxed">
              {day1.score > day2.score
                ? `Ngay ${formatDate(date1)} tot hon voi diem ${day1.score}/100. ${day1.reason}`
                : day2.score > day1.score
                  ? `Ngay ${formatDate(date2)} tot hon voi diem ${day2.score}/100. ${day2.reason}`
                  : "Hai ngay tuong duong — chon ngay nao tien hon cho ban."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
