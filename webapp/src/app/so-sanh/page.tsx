"use client";

import { useState } from "react";
import { useRequireProfile } from "@/lib/use-require-profile";
import { useApi } from "@/lib/use-api";
import { fetchDayDetail, type DayDetailResponse } from "@/lib/api";
import { BracketText } from "@/components/bracket-text";
import { ScoreBadge } from "@/components/score-badge";
import { formatDateShort } from "@/lib/utils";

export default function SoSanhPage() {
  const { profile, isReady } = useRequireProfile();

  const [date1, setDate1] = useState("");
  const [date2, setDate2] = useState("");
  const [comparing, setComparing] = useState(false);

  const { data: day1, loading: l1, error: e1 } = useApi(
    comparing && date1 && profile
      ? () => fetchDayDetail({ birthDate: profile.birthDate, birthHour: profile.birthHour, gender: profile.gender, date: date1 })
      : null,
    [comparing, date1]
  );

  const { data: day2, loading: l2, error: e2 } = useApi(
    comparing && date2 && profile
      ? () => fetchDayDetail({ birthDate: profile.birthDate, birthHour: profile.birthHour, gender: profile.gender, date: date2 })
      : null,
    [comparing, date2]
  );

  if (!isReady) return null;

  const handleCompare = () => {
    if (date1 && date2) setComparing(true);
  };

  const loading = l1 || l2;
  const error = e1 || e2;

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

      {!comparing && (
        <div className="space-y-6">
          <div>
            <label htmlFor="compare-d1" className="mono-label block mb-3">Ngay thu nhat</label>
            <input id="compare-d1" type="date" value={date1} onChange={(e) => setDate1(e.target.value)}
              className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg" />
          </div>
          <div>
            <label htmlFor="compare-d2" className="mono-label block mb-3">Ngay thu hai</label>
            <input id="compare-d2" type="date" value={date2} onChange={(e) => setDate2(e.target.value)}
              className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg" />
          </div>
          <button type="button" onClick={handleCompare}
            className={`btn-primary w-full ${!date1 || !date2 ? "opacity-30 cursor-not-allowed" : ""}`}
            disabled={!date1 || !date2}>
            So sanh
          </button>
        </div>
      )}

      {comparing && loading && (
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="mono-label text-accent">Dang phan tich...</div>
        </div>
      )}

      {comparing && error && (
        <div className="page-enter">
          <button type="button" onClick={() => setComparing(false)} className="mono-label mb-6 flex items-center gap-1">&larr; Chon lai</button>
          <div className="flex flex-col items-center py-20 gap-2">
            <div className="mono-label text-bad">Loi</div>
            <p className="text-xs text-fg-muted">{error}</p>
          </div>
        </div>
      )}

      {comparing && day1 && day2 && !loading && (
        <div className="page-enter">
          <button type="button" onClick={() => setComparing(false)} className="mono-label mb-6 flex items-center gap-1">&larr; Chon lai</button>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className={`text-center p-3 ${day1.score > day2.score ? "border border-accent" : "border border-border"}`}>
              <div className="text-sm font-bold">{formatDateShort(date1)}</div>
              <div className="mono-label">{day1.can_chi}</div>
            </div>
            <div className={`text-center p-3 ${day2.score > day1.score ? "border border-accent" : "border border-border"}`}>
              <div className="text-sm font-bold">{formatDateShort(date2)}</div>
              <div className="mono-label">{day2.can_chi}</div>
            </div>
          </div>

          <div className="border-t border-b border-border py-5 mb-6">
            <div className="mono-label mb-3 text-center">Diem tong</div>
            <div className="grid grid-cols-2 gap-3 text-center">
              <ScoreBadge score={day1.score} grade={day1.grade as "A"|"B"|"C"|"D"} size="md" />
              <ScoreBadge score={day2.score} grade={day2.grade as "A"|"B"|"C"|"D"} size="md" />
            </div>
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="score-bar"><div className="score-bar-fill" style={{ width: `${day1.score}%` }} /></div>
              <div className="score-bar"><div className="score-bar-fill" style={{ width: `${day2.score}%` }} /></div>
            </div>
          </div>

          {[
            { label: "Hoang Dao", v1: day1.hoang_dao ? "Co" : "Khong", v2: day2.hoang_dao ? "Co" : "Khong", w1: day1.hoang_dao, w2: day2.hoang_dao },
            { label: "Truc", v1: day1.truc_name, v2: day2.truc_name, w1: day1.truc_score > 0, w2: day2.truc_score > 0 },
            { label: "Sao 28 Tu", v1: `${day1.sao_28} (${day1.sao_element})`, v2: `${day2.sao_28} (${day2.sao_element})`, w1: true, w2: true },
            { label: "Hung ngay", v1: day1.hung_ngay.length === 0 ? "Khong" : day1.hung_ngay.join(", "), v2: day2.hung_ngay.length === 0 ? "Khong" : day2.hung_ngay.join(", "), w1: day1.hung_ngay.length === 0, w2: day2.hung_ngay.length === 0 },
          ].map((row) => (
            <div key={row.label} className="grid grid-cols-[1fr_auto_1fr] gap-2 mb-3 items-center">
              <div className={`text-xs text-center p-2 ${row.w1 && !row.w2 ? "bg-good/10" : ""}`}>{row.v1}</div>
              <div className="mono-label text-center min-w-[70px]">{row.label}</div>
              <div className={`text-xs text-center p-2 ${row.w2 && !row.w1 ? "bg-good/10" : ""}`}>{row.v2}</div>
            </div>
          ))}

          <div className="border-t border-border pt-5 mt-4 mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="mono-label text-good mb-2">Nen lam</div>
                {day1.good_for.map((g) => (<div key={g} className="text-xs mb-1">{g}</div>))}
              </div>
              <div>
                <div className="mono-label text-good mb-2">Nen lam</div>
                {day2.good_for.map((g) => (<div key={g} className="text-xs mb-1">{g}</div>))}
              </div>
            </div>
          </div>

          <div className="border-t border-border pt-5 mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="mono-label mb-2">Gio tot</div>
                <div className="flex flex-wrap gap-1">
                  {day1.good_hours.map((h) => (
                    <span key={h} className="mono-label px-2 py-1 bg-good/10 text-good">{h}</span>
                  ))}
                </div>
              </div>
              <div>
                <div className="mono-label mb-2">Gio tot</div>
                <div className="flex flex-wrap gap-1">
                  {day2.good_hours.map((h) => (
                    <span key={h} className="mono-label px-2 py-1 bg-good/10 text-good">{h}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-bg-card p-4 mb-6">
            <div className="mono-label text-accent mb-2">Ket luan</div>
            <p className="text-xs leading-relaxed">
              {day1.score > day2.score
                ? `Ngay ${formatDateShort(date1)} tot hon voi diem ${day1.score}/100. ${day1.reason}`
                : day2.score > day1.score
                  ? `Ngay ${formatDateShort(date2)} tot hon voi diem ${day2.score}/100. ${day2.reason}`
                  : "Hai ngay tuong duong — chon ngay nao tien hon cho ban."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
