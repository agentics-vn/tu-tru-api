"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireProfile } from "@/lib/use-require-profile";
import { BIRTH_HOURS } from "@/lib/mock-data";
import { useApi } from "@/lib/use-api";
import { fetchHopTuoi } from "@/lib/api";
import { BracketText } from "@/components/bracket-text";
import { ScoreBadge } from "@/components/score-badge";
import { DateInput, validateDateInput } from "@/components/date-input";

type Step = "input" | "result";

export default function HopTuoiPage() {
  const { profile, isReady } = useRequireProfile();
  const router = useRouter();

  const [step, setStep] = useState<Step>("input");
  const [day2, setDay2] = useState("");
  const [month2, setMonth2] = useState("");
  const [year2, setYear2] = useState("");
  const [hour2, setHour2] = useState("unknown");
  const [gender2, setGender2] = useState<"nam" | "nu">("nu");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const person2Date = year2 && month2 && day2
    ? `${year2}-${month2.padStart(2, "0")}-${day2.padStart(2, "0")}`
    : "";

  const { data: result, loading, error: apiError } = useApi(
    submitted && step === "result" && profile && person2Date
      ? () =>
          fetchHopTuoi({
            person1BirthDate: profile.birthDate,
            person1BirthHour: profile.birthHour,
            person1Gender: profile.gender,
            person2BirthDate: person2Date,
            person2BirthHour: hour2,
            person2Gender: gender2,
          })
      : null,
    [submitted, person2Date, hour2, gender2]
  );

  if (!isReady || !profile) return null;

  const handleSubmit = () => {
    const validationError = validateDateInput(day2, month2, year2);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");
    setSubmitted(true);
    setStep("result");
  };

  const handleBack = () => {
    setStep("input");
    setSubmitted(false);
  };

  const RELATION_COLORS: Record<string, string> = {
    "Tương Sinh": "text-good",
    "Tương Khắc": "text-bad",
    "Bình Hòa": "text-accent",
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

          <div className="border border-border p-4 mb-6">
            <div className="mono-label text-accent mb-2">Nguoi 1 (ban)</div>
            <div className="text-sm font-bold">{profile.birthDate}</div>
            <div className="mono-label mt-1">
              {profile.gender === "nam" ? "Nam" : "Nu"} —{" "}
              {profile.birthHour === "unknown" ? "Khong ro gio sinh" : `Gio ${profile.birthHour}`}
            </div>
          </div>

          <div className="space-y-6">
            <div className="mono-label text-accent">Nguoi 2 (doi phuong)</div>

            <div>
              <label className="mono-label block mb-3">Ngay sinh</label>
              <DateInput
                day={day2} month={month2} year={year2}
                onDayChange={(v) => { setDay2(v); setError(""); }}
                onMonthChange={(v) => { setMonth2(v); setError(""); }}
                onYearChange={(v) => { setYear2(v); setError(""); }}
                error={error}
              />
            </div>

            <div>
              <label htmlFor="hop-tuoi-hour" className="mono-label block mb-3">Gio sinh</label>
              <select
                id="hop-tuoi-hour"
                value={hour2}
                onChange={(e) => setHour2(e.target.value)}
                className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg transition-colors cursor-pointer"
              >
                {BIRTH_HOURS.map((h) => (
                  <option key={h.value} value={h.value}>{h.label}</option>
                ))}
              </select>
            </div>

            <fieldset>
              <legend className="mono-label mb-3">Gioi tinh</legend>
              <div className="flex gap-0" role="radiogroup">
                <button
                  type="button" role="radio" aria-checked={gender2 === "nam"}
                  onClick={() => setGender2("nam")}
                  className={`flex-1 py-3 text-xs uppercase tracking-widest border transition-colors ${gender2 === "nam" ? "bg-fg text-bg border-fg" : "bg-transparent text-fg-muted border-border"}`}
                >Nam</button>
                <button
                  type="button" role="radio" aria-checked={gender2 === "nu"}
                  onClick={() => setGender2("nu")}
                  className={`flex-1 py-3 text-xs uppercase tracking-widest border border-l-0 transition-colors ${gender2 === "nu" ? "bg-fg text-bg border-fg" : "bg-transparent text-fg-muted border-border"}`}
                >Nu</button>
              </div>
            </fieldset>

            <button type="button" onClick={handleSubmit} className="btn-primary w-full">
              Xem ket qua hop tuoi
            </button>
          </div>
        </>
      )}

      {step === "result" && loading && (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="mono-label text-accent">Dang phan tich...</div>
        </div>
      )}

      {step === "result" && apiError && (
        <div className="page-enter">
          <button type="button" onClick={handleBack} className="mono-label mb-6 flex items-center gap-1">&larr; Nhap lai</button>
          <div className="flex flex-col items-center py-20 gap-2">
            <div className="mono-label text-bad">Loi</div>
            <p className="text-xs text-fg-muted">{apiError}</p>
          </div>
        </div>
      )}

      {step === "result" && result && !loading && (
        <div className="page-enter">
          <button type="button" onClick={handleBack} className="mono-label mb-6 flex items-center gap-1">&larr; Nhap lai</button>

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

          <div className="border-t border-b border-border py-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <div className="mono-label">Diem tuong hop tong</div>
              <span className={`mono-label px-2 py-0.5 ${RELATION_COLORS[result.ngu_hanh_relation] || "text-fg-muted"}`}>
                {result.ngu_hanh_relation}
              </span>
            </div>
            <ScoreBadge score={result.overall_score} grade={result.grade as "A"|"B"|"C"|"D"} size="lg" />
            <div className="score-bar mt-4">
              <div className="score-bar-fill" style={{ width: `${result.overall_score}%` }} />
            </div>
          </div>

          <div className="mb-8 space-y-4">
            {result.details.map((d) => (
              <div key={d.category} className="border-t border-border pt-3">
                <div className="flex justify-between mb-1">
                  <span className="mono-label">{d.category}</span>
                  <span className="mono-label font-medium text-fg">{d.score}/100</span>
                </div>
                <div className="score-bar mb-2">
                  <div className="score-bar-fill" style={{ width: `${d.score}%` }} />
                </div>
                <p className="text-xs text-fg-muted">{d.description}</p>
              </div>
            ))}
          </div>

          <div className="border-t border-border pt-5 mb-6">
            <div className="mono-label text-accent mb-2">Nhan dinh</div>
            <p className="text-sm leading-relaxed text-fg-muted">&ldquo;{result.summary}&rdquo;</p>
          </div>

          <div className="bg-bg-card p-4 mb-8">
            <div className="mono-label text-good mb-2">Loi khuyen</div>
            <p className="text-xs leading-relaxed">{result.advice}</p>
          </div>

          <div className="space-y-3">
            <button type="button" onClick={() => router.push("/chon-ngay")} className="btn-primary w-full">
              Chon ngay cuoi tot nhat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
