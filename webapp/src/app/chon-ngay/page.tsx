"use client";

import { useState, useMemo } from "react";
import { useRequireProfile } from "@/lib/use-require-profile";
import {
  INTENT_OPTIONS,
  mockChonNgayResult,
  resetMockSeed,
} from "@/lib/mock-data";
import { DayCard } from "@/components/day-card";
import { BracketText } from "@/components/bracket-text";

type Step = "select" | "result";

export default function ChonNgayPage() {
  const { isReady } = useRequireProfile();

  const [step, setStep] = useState<Step>("select");
  const [intent, setIntent] = useState("");
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  const threeMonths = new Date(now.getFullYear(), now.getMonth() + 3, 0);
  const [dateFrom, setDateFrom] = useState(
    nextMonth.toISOString().slice(0, 10)
  );
  const [dateTo, setDateTo] = useState(
    threeMonths.toISOString().slice(0, 10)
  );
  const [rangeError, setRangeError] = useState("");
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

  // Only generate top 1 for free — premium data not in DOM at all
  const result = useMemo(() => {
    if (step !== "result" || !intent) return null;
    resetMockSeed(intent.length * 1000 + 7);
    return mockChonNgayResult(
      INTENT_OPTIONS.find((i) => i.value === intent)?.label || intent
    );
  }, [step, intent]);

  if (!isReady) return null;

  const handleSubmit = () => {
    if (!intent) return;
    const from = new Date(dateFrom);
    const to = new Date(dateTo);
    if (from >= to) {
      setRangeError("Ngay bat dau phai truoc ngay ket thuc.");
      return;
    }
    const diffDays = Math.ceil(
      (to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24)
    );
    if (diffDays > 90) {
      setRangeError("Khoang thoi gian toi da la 90 ngay.");
      return;
    }
    setRangeError("");
    setStep("result");
  };

  // Separate free and premium data — premium not rendered in DOM
  const freeResult = result?.recommended.slice(0, 1) ?? [];
  const premiumCount = (result?.recommended.length ?? 0) - 1;

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

          {/* Intent selection */}
          <div className="mb-8">
            <label className="mono-label block mb-4">Ban muon lam gi?</label>
            <div className="grid grid-cols-3 gap-0" role="radiogroup">
              {INTENT_OPTIONS.map((opt) => (
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

          {/* Date range */}
          <div className="mb-8">
            <label className="mono-label block mb-3">Khoang thoi gian</label>
            <div className="flex items-center gap-3">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  setRangeError("");
                }}
                aria-label="Ngay bat dau"
                className="flex-1 bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
              />
              <span className="mono-label">&rarr;</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  setRangeError("");
                }}
                aria-label="Ngay ket thuc"
                className="flex-1 bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
              />
            </div>
            {rangeError && (
              <p className="mono-label text-bad mt-2" role="alert">
                {rangeError}
              </p>
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

      {step === "result" && result && (
        <div className="page-enter">
          <button
            type="button"
            onClick={() => setStep("select")}
            className="mono-label mb-6 flex items-center gap-1"
          >
            &larr; Chon lai
          </button>

          <h2 className="heading-display text-xl mb-2">{result.intent}</h2>
          <div className="mono-label mb-6">
            {result.range.from} &rarr; {result.range.to} — {result.totalDays}{" "}
            ngay
          </div>

          {/* Funnel stats */}
          <div className="border-t border-b border-border py-4 mb-6 space-y-2">
            <div className="flex justify-between">
              <span className="mono-label">Da phan tich</span>
              <span className="mono-label font-medium text-fg">
                {result.totalDays} ngay
              </span>
            </div>
            <div className="flex justify-between">
              <span className="mono-label">Qua vong 1 (lich)</span>
              <span className="mono-label font-medium text-fg">
                {result.layer1Pass} ngay
              </span>
            </div>
            <div className="flex justify-between">
              <span className="mono-label">Qua vong 2 (hop menh)</span>
              <span className="mono-label font-medium text-fg">
                {result.layer2Pass} ngay
              </span>
            </div>
            <div className="flex justify-between">
              <span className="mono-label">Xep hang vong 3</span>
              <span className="mono-label font-medium text-accent">
                Top {result.recommended.length}
              </span>
            </div>
          </div>

          {/* Free result — top 1 only */}
          <div className="mb-4">
            {freeResult.map((day, idx) => (
              <DayCard
                key={day.date}
                day={day}
                rank={idx + 1}
                expanded={expandedIdx === idx}
                onToggle={() =>
                  setExpandedIdx(expandedIdx === idx ? null : idx)
                }
              />
            ))}
          </div>

          {/* Premium paywall — data NOT in DOM */}
          {premiumCount > 0 && (
            <div className="border border-accent p-5 text-center mb-6">
              <div className="mono-label text-accent mb-2">Premium</div>
              <p className="text-sm mb-3">
                Con {premiumCount} ngay tot nua trong top{" "}
                {result.recommended.length}
              </p>
              <button type="button" className="btn-primary">
                Mo khoa tat ca — 79K/thang
              </button>
            </div>
          )}

          {/* Days to avoid */}
          {result.avoid.length > 0 && (
            <div className="mb-8">
              <div className="mono-label text-bad mb-3">Ngay can tranh</div>
              {result.avoid.map((a) => (
                <div
                  key={a.date}
                  className="flex justify-between items-center py-2 border-t border-border"
                >
                  <span className="text-sm">{a.date}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-fg-muted">{a.reason}</span>
                    <span
                      className={`mono-label px-1.5 py-0.5 ${
                        a.severity === 3
                          ? "bg-bad text-bg"
                          : "bg-warn/20 text-warn"
                      }`}
                    >
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
