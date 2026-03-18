"use client";

import { useState } from "react";
import { useRequireProfile } from "@/lib/use-require-profile";
import { API_INTENTS } from "@/lib/mock-data";
import { useApi } from "@/lib/use-api";
import { fetchChonNgay } from "@/lib/api";
import { DayCard } from "@/components/day-card";
import { BracketText } from "@/components/bracket-text";

type Step = "select" | "result";

export default function ChonNgayPage() {
  const { profile, isReady } = useRequireProfile();

  const [step, setStep] = useState<Step>("select");
  const [intent, setIntent] = useState("");
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  const threeMonths = new Date(now.getFullYear(), now.getMonth() + 3, 0);
  const [dateFrom, setDateFrom] = useState(nextMonth.toISOString().slice(0, 10));
  const [dateTo, setDateTo] = useState(threeMonths.toISOString().slice(0, 10));
  const [rangeError, setRangeError] = useState("");
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);
  const [submitted, setSubmitted] = useState(false);

  const { data: result, loading, error } = useApi(
    submitted && step === "result" && profile
      ? () =>
          fetchChonNgay({
            birthDate: profile.birthDate,
            birthHour: profile.birthHour,
            gender: profile.gender,
            intent,
            rangeStart: dateFrom,
            rangeEnd: dateTo,
            topN: 5,
          })
      : null,
    [submitted, intent, dateFrom, dateTo]
  );

  if (!isReady) return null;

  const handleSubmit = () => {
    if (!intent) return;
    const from = new Date(dateFrom);
    const to = new Date(dateTo);
    if (from >= to) {
      setRangeError("Ngay bat dau phai truoc ngay ket thuc.");
      return;
    }
    const diffDays = Math.ceil((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays > 90) {
      setRangeError("Khoang thoi gian toi da la 90 ngay.");
      return;
    }
    setRangeError("");
    setSubmitted(true);
    setStep("result");
  };

  const handleBack = () => {
    setStep("select");
    setSubmitted(false);
  };

  const intentLabel = API_INTENTS.find((i) => i.value === intent)?.label || intent;

  // Map API response to DayCard format
  const recommended = result?.recommended_dates.map((d) => ({
    date: d.date,
    lunarDate: d.lunar_date,
    canChi: "",
    hoangDao: true,
    trucName: d.truc,
    trucScore: 2,
    sao28: d.sao_cat.join(", "),
    saoElement: d.nguhanh_day,
    score: d.score,
    grade: d.grade as "A" | "B" | "C" | "D",
    goodFor: d.sao_cat,
    badFor: d.sao_hung,
    goodHours: d.time_slots,
    badHours: [] as string[],
    reason: d.reason_vi || d.summary_vi,
    hungNgay: [] as string[],
  })) ?? [];

  const freeResult = recommended.slice(0, 1);
  const premiumCount = recommended.length - 1;

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Chon ngay</div>
      </header>

      {step === "select" && (
        <>
          <div className="flex items-start gap-6 mb-10">
            <h1 className="heading-display text-[2rem] leading-tight flex-1">
              Chon ngay
              <br />
              tot nhat
            </h1>
            <BracketText className="mt-1">
              <div className="flex flex-col items-center text-base">
                <span>chon</span>
                <span>ngay</span>
              </div>
            </BracketText>
          </div>

          <div className="mb-8">
            <label className="mono-label block mb-4">Ban muon lam gi?</label>
            <div className="grid grid-cols-3 gap-0" role="radiogroup">
              {API_INTENTS.map((opt) => (
                <button
                  type="button"
                  key={opt.value}
                  role="radio"
                  aria-checked={intent === opt.value}
                  onClick={() => setIntent(opt.value)}
                  className={`py-4 border text-xs transition-colors ${
                    intent === opt.value
                      ? "bg-fg text-bg border-fg"
                      : "bg-transparent text-fg border-border"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-8">
            <label className="mono-label block mb-3">Khoang thoi gian</label>
            <div className="flex items-center gap-3">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); setRangeError(""); }}
                aria-label="Ngay bat dau"
                className="flex-1 bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
              />
              <span className="mono-label">&rarr;</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => { setDateTo(e.target.value); setRangeError(""); }}
                aria-label="Ngay ket thuc"
                className="flex-1 bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
              />
            </div>
            {rangeError && (
              <p className="mono-label text-bad mt-2" role="alert">{rangeError}</p>
            )}
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            className={`btn-primary w-full ${!intent ? "opacity-30 cursor-not-allowed" : ""}`}
            disabled={!intent}
            aria-disabled={!intent}
          >
            Tim ngay tot nhat
          </button>
        </>
      )}

      {step === "result" && loading && (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="mono-label text-accent">Dang phan tich...</div>
        </div>
      )}

      {step === "result" && error && (
        <div className="page-enter">
          <button type="button" onClick={handleBack} className="mono-label mb-6 flex items-center gap-1">
            &larr; Chon lai
          </button>
          <div className="flex flex-col items-center py-20 gap-2">
            <div className="mono-label text-bad">Khong the phan tich</div>
            <p className="text-xs text-fg-muted text-center">{error}</p>
          </div>
        </div>
      )}

      {step === "result" && result && !loading && (
        <div className="page-enter">
          <button type="button" onClick={handleBack} className="mono-label mb-6 flex items-center gap-1">
            &larr; Chon lai
          </button>

          <h2 className="heading-display text-xl mb-2">{intentLabel}</h2>
          <div className="mono-label mb-6">
            {result.meta.range_scanned.from} &rarr; {result.meta.range_scanned.to} — {result.meta.total_days_scanned} ngay
          </div>

          <div className="border-t border-b border-border py-4 mb-6 space-y-2">
            <div className="flex justify-between">
              <span className="mono-label">Da phan tich</span>
              <span className="mono-label font-medium text-fg">{result.meta.total_days_scanned} ngay</span>
            </div>
            <div className="flex justify-between">
              <span className="mono-label">Qua vong 1 (lich)</span>
              <span className="mono-label font-medium text-fg">{result.meta.days_passed_layer1} ngay</span>
            </div>
            <div className="flex justify-between">
              <span className="mono-label">Qua vong 2 (hop menh)</span>
              <span className="mono-label font-medium text-fg">{result.meta.days_passed_layer2} ngay</span>
            </div>
            <div className="flex justify-between">
              <span className="mono-label">Xep hang vong 3</span>
              <span className="mono-label font-medium text-accent">Top {recommended.length}</span>
            </div>
          </div>

          {result.meta.bat_tu_summary && (
            <div className="mono-label mb-6">
              Menh {result.meta.bat_tu_summary.ngu_hanh_menh} — Dung Than {result.meta.bat_tu_summary.duong_than}
            </div>
          )}

          <div className="mb-4">
            {freeResult.map((day, idx) => (
              <DayCard
                key={day.date}
                day={day}
                rank={idx + 1}
                expanded={expandedIdx === idx}
                onToggle={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
              />
            ))}
          </div>

          {premiumCount > 0 && (
            <div className="border border-accent p-5 text-center mb-6">
              <div className="mono-label text-accent mb-2">Premium</div>
              <p className="text-sm mb-3">Con {premiumCount} ngay tot nua trong top {recommended.length}</p>
              <button type="button" className="btn-primary">Mo khoa tat ca — 79K/thang</button>
            </div>
          )}

          {result.dates_to_avoid.length > 0 && (
            <div className="mb-8">
              <div className="mono-label text-bad mb-3">Ngay can tranh</div>
              {result.dates_to_avoid.map((a) => (
                <div key={a.date} className="flex justify-between items-center py-2 border-t border-border">
                  <span className="text-sm">{a.date}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-fg-muted">{a.reason_vi}</span>
                    <span className={`mono-label px-1.5 py-0.5 ${a.severity === 3 ? "bg-bad text-bg" : "bg-warn/20 text-warn"}`}>
                      {a.severity === 3 ? "Tuyet doi" : "Canh bao"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
