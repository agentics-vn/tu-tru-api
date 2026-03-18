"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { INTENT_OPTIONS, mockChonNgayResult } from "@/lib/mock-data";
import { DayCard } from "@/components/day-card";
import { BracketText } from "@/components/bracket-text";

type Step = "select" | "result";

export default function ChonNgayPage() {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();

  const [step, setStep] = useState<Step>("select");
  const [intent, setIntent] = useState("");
  const [dateFrom, setDateFrom] = useState("2026-04-01");
  const [dateTo, setDateTo] = useState("2026-06-30");
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

  const result = useMemo(() => {
    if (step !== "result" || !intent) return null;
    return mockChonNgayResult(
      INTENT_OPTIONS.find((i) => i.value === intent)?.label || intent
    );
  }, [step, intent]);

  if (isLoaded && !profile) {
    router.replace("/");
    return null;
  }
  if (!isLoaded) return null;

  return (
    <div className="px-6 py-6 page-enter">
      {/* Header */}
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Chon ngay</div>
      </header>

      {step === "select" && (
        <>
          {/* Title */}
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
            <div className="grid grid-cols-3 gap-0">
              {INTENT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setIntent(opt.value)}
                  className={`
                    py-4 border text-xs transition-colors
                    ${
                      intent === opt.value
                        ? "bg-fg text-bg border-fg"
                        : "bg-transparent text-fg border-border"
                    }
                  `}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Date range */}
          <div className="mb-8">
            <label className="mono-label block mb-3">
              Khoang thoi gian
            </label>
            <div className="flex items-center gap-3">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="flex-1 bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
              />
              <span className="mono-label">&rarr;</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="flex-1 bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg"
              />
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={() => intent && setStep("result")}
            className={`btn-primary w-full ${!intent ? "opacity-30 cursor-not-allowed" : ""}`}
            disabled={!intent}
          >
            Tim ngay tot nhat
          </button>
        </>
      )}

      {step === "result" && result && (
        <div className="page-enter">
          {/* Back */}
          <button
            onClick={() => setStep("select")}
            className="mono-label mb-6 flex items-center gap-1"
          >
            &larr; Chon lai
          </button>

          {/* Title */}
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

          {/* Recommended days */}
          <div className="mb-8">
            {result.recommended.map((day, idx) => {
              const isBlurred = idx > 0; // Only first is free
              return (
                <div key={day.date} className={isBlurred ? "relative" : ""}>
                  {isBlurred && idx === 1 && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center">
                      <div className="text-center">
                        <div className="mono-label text-accent mb-2">
                          Premium
                        </div>
                        <button className="btn-primary text-[0.6rem] px-6 py-2">
                          Mo khoa top {result.recommended.length}
                        </button>
                      </div>
                    </div>
                  )}
                  <div className={isBlurred ? "blur-paywall" : ""}>
                    <DayCard
                      day={day}
                      rank={idx + 1}
                      expanded={expandedIdx === idx && !isBlurred}
                      onToggle={() =>
                        !isBlurred &&
                        setExpandedIdx(expandedIdx === idx ? null : idx)
                      }
                    />
                  </div>
                </div>
              );
            })}
          </div>

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
