"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { BIRTH_HOURS, mockHopTuoiResult } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";
import { ScoreBadge } from "@/components/score-badge";

type Step = "input" | "result";

export default function HopTuoiPage() {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();

  const [step, setStep] = useState<Step>("input");
  const [day2, setDay2] = useState("");
  const [month2, setMonth2] = useState("");
  const [year2, setYear2] = useState("");
  const [hour2, setHour2] = useState("unknown");
  const [gender2, setGender2] = useState<"nam" | "nu">("nu");

  const result = useMemo(() => {
    if (step !== "result" || !profile) return null;
    const d2 = `${year2}-${month2.padStart(2, "0")}-${day2.padStart(2, "0")}`;
    return mockHopTuoiResult(profile.birthDate, d2);
  }, [step, profile, year2, month2, day2]);

  if (isLoaded && !profile) {
    router.replace("/");
    return null;
  }
  if (!isLoaded) return null;

  const handleSubmit = () => {
    const d = parseInt(day2);
    const m = parseInt(month2);
    const y = parseInt(year2);
    if (!d || !m || !y || y < 1920 || y > 2020) return;
    setStep("result");
  };

  const RELATION_COLORS: Record<string, string> = {
    "Tuong Sinh": "text-good",
    "Tuong Khac": "text-bad",
    "Binh Hoa": "text-accent",
  };

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Hop tuoi</div>
      </header>

      {step === "input" && (
        <>
          <div className="flex items-start justify-between mb-10">
            <div>
              <h1 className="heading-display text-[2rem] leading-tight">
                Hop tuoi
                <br />
                doi lua
              </h1>
              <p className="text-xs text-fg-muted mt-2 max-w-[240px] leading-relaxed">
                So sanh tuong hop giua hai la so Tu Tru. Xem ngu hanh, thien can,
                dia chi va loi khuyen phong thuy.
              </p>
            </div>
            <BracketText className="mt-1">
              <div className="flex flex-col items-center text-base">
                <span>hop</span>
                <span>tuoi</span>
              </div>
            </BracketText>
          </div>

          {/* Person 1 — from profile */}
          <div className="border border-border p-4 mb-6">
            <div className="mono-label text-accent mb-2">Nguoi 1 (ban)</div>
            <div className="text-sm font-bold">{profile!.birthDate}</div>
            <div className="mono-label mt-1">
              {profile!.gender === "nam" ? "Nam" : "Nu"} —{" "}
              {profile!.birthHour === "unknown"
                ? "Khong ro gio sinh"
                : `Gio ${profile!.birthHour}`}
            </div>
          </div>

          {/* Person 2 — input */}
          <div className="space-y-6">
            <div className="mono-label text-accent">Nguoi 2 (doi phuong)</div>

            <div>
              <label className="mono-label block mb-3">Ngay sinh</label>
              <div className="flex gap-3">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={2}
                  placeholder="DD"
                  value={day2}
                  onChange={(e) => setDay2(e.target.value.replace(/\D/g, ""))}
                  className="flex-1 bg-transparent border-b border-border py-3 text-center text-lg font-bold focus:outline-none focus:border-fg transition-colors placeholder:text-border"
                />
                <span className="text-border self-end pb-3">/</span>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={2}
                  placeholder="MM"
                  value={month2}
                  onChange={(e) => setMonth2(e.target.value.replace(/\D/g, ""))}
                  className="flex-1 bg-transparent border-b border-border py-3 text-center text-lg font-bold focus:outline-none focus:border-fg transition-colors placeholder:text-border"
                />
                <span className="text-border self-end pb-3">/</span>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={4}
                  placeholder="YYYY"
                  value={year2}
                  onChange={(e) => setYear2(e.target.value.replace(/\D/g, ""))}
                  className="flex-[1.5] bg-transparent border-b border-border py-3 text-center text-lg font-bold focus:outline-none focus:border-fg transition-colors placeholder:text-border"
                />
              </div>
            </div>

            <div>
              <label className="mono-label block mb-3">Gio sinh</label>
              <select
                value={hour2}
                onChange={(e) => setHour2(e.target.value)}
                className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg transition-colors appearance-none cursor-pointer"
              >
                {BIRTH_HOURS.map((h) => (
                  <option key={h.value} value={h.value}>
                    {h.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mono-label block mb-3">Gioi tinh</label>
              <div className="flex gap-0">
                <button
                  onClick={() => setGender2("nam")}
                  className={`flex-1 py-3 text-xs uppercase tracking-widest border transition-colors ${
                    gender2 === "nam"
                      ? "bg-fg text-bg border-fg"
                      : "bg-transparent text-fg-muted border-border"
                  }`}
                >
                  Nam
                </button>
                <button
                  onClick={() => setGender2("nu")}
                  className={`flex-1 py-3 text-xs uppercase tracking-widest border border-l-0 transition-colors ${
                    gender2 === "nu"
                      ? "bg-fg text-bg border-fg"
                      : "bg-transparent text-fg-muted border-border"
                  }`}
                >
                  Nu
                </button>
              </div>
            </div>

            <button onClick={handleSubmit} className="btn-primary w-full">
              Xem ket qua hop tuoi
            </button>
          </div>
        </>
      )}

      {step === "result" && result && (
        <div className="page-enter">
          <button
            onClick={() => setStep("input")}
            className="mono-label mb-6 flex items-center gap-1"
          >
            &larr; Nhap lai
          </button>

          {/* Two persons */}
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="border border-border p-3">
              <div className="mono-label mb-1">Nguoi 1</div>
              <div className="text-xs font-bold">{result.person1.nhatChu}</div>
              <div className="mono-label mt-0.5">{result.person1.menh}</div>
              <div className="mono-label text-accent">{result.person1.hanh}</div>
            </div>
            <div className="border border-border p-3">
              <div className="mono-label mb-1">Nguoi 2</div>
              <div className="text-xs font-bold">{result.person2.nhatChu}</div>
              <div className="mono-label mt-0.5">{result.person2.menh}</div>
              <div className="mono-label text-accent">{result.person2.hanh}</div>
            </div>
          </div>

          {/* Overall score */}
          <div className="border-t border-b border-border py-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <div className="mono-label">Diem tuong hop tong</div>
              <span
                className={`mono-label px-2 py-0.5 ${RELATION_COLORS[result.nguHanhRelation] || "text-fg-muted"}`}
              >
                {result.nguHanhRelation}
              </span>
            </div>
            <ScoreBadge
              score={result.overallScore}
              grade={result.grade}
              size="lg"
            />
            <div className="score-bar mt-4">
              <div
                className="score-bar-fill"
                style={{ width: `${result.overallScore}%` }}
              />
            </div>
          </div>

          {/* Detail categories */}
          <div className="mb-8 space-y-4">
            {result.details.map((d) => (
              <div key={d.category} className="border-t border-border pt-3">
                <div className="flex justify-between mb-1">
                  <span className="mono-label">{d.category}</span>
                  <span className="mono-label font-medium text-fg">
                    {d.score}/100
                  </span>
                </div>
                <div className="score-bar mb-2">
                  <div
                    className="score-bar-fill"
                    style={{ width: `${d.score}%` }}
                  />
                </div>
                <p className="text-xs text-fg-muted">{d.description}</p>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="border-t border-border pt-5 mb-6">
            <div className="mono-label text-accent mb-2">Nhan dinh</div>
            <p className="text-sm leading-relaxed text-fg-muted">
              &ldquo;{result.summary}&rdquo;
            </p>
          </div>

          {/* Advice */}
          <div className="bg-bg-card p-4 mb-8">
            <div className="mono-label text-good mb-2">Loi khuyen</div>
            <p className="text-xs leading-relaxed">{result.advice}</p>
          </div>

          {/* CTAs */}
          <div className="space-y-3">
            <button
              onClick={() => router.push("/chon-ngay")}
              className="btn-primary w-full"
            >
              Chon ngay cuoi tot nhat
            </button>
            <button className="mono-label w-full py-3 text-center text-accent">
              Chia se ket qua
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
