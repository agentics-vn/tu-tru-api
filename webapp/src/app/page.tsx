"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { BIRTH_HOURS } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";
import { DateInput, validateDateInput } from "@/components/date-input";

export default function LandingPage() {
  const router = useRouter();
  const { profile, setProfile, isLoaded } = useProfile();

  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [hour, setHour] = useState("unknown");
  const [gender, setGender] = useState<"nam" | "nu">("nam");
  const [error, setError] = useState("");

  // Redirect if profile exists — via useEffect, not during render
  useEffect(() => {
    if (isLoaded && profile) {
      router.replace("/hom-nay");
    }
  }, [isLoaded, profile, router]);

  if (!isLoaded || profile) return null;

  const handleSubmit = () => {
    const validationError = validateDateInput(day, month, year);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");

    const d = parseInt(day);
    const m = parseInt(month);
    const y = parseInt(year);
    const birthDate = `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    setProfile({ birthDate, birthHour: hour, gender });
    router.push("/hom-nay");
  };

  return (
    <div className="min-h-dvh flex flex-col justify-between px-6 py-8 page-enter">
      {/* Header */}
      <header className="flex justify-between items-start">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">[{new Date().getFullYear()}]</div>
      </header>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center -mt-8">
        <BracketText>
          <div className="flex flex-col items-center gap-1">
            <span>tu</span>
            <span>tru</span>
          </div>
        </BracketText>

        <h1 className="heading-display text-[2.5rem] text-center mt-8 mb-3">
          BIET MENH
          <br />
          SONG CHU DONG
        </h1>

        <p className="text-xs text-fg-muted text-center max-w-[260px] leading-relaxed">
          Chon ngay tot dua tren la so ca nhan.
          <br />
          Khong can dang ky. Nhap ngay sinh de bat dau.
        </p>
      </div>

      {/* Form */}
      <div className="space-y-6">
        {/* Date inputs */}
        <div>
          <label className="mono-label block mb-3" id="birth-date-label">
            Ngay sinh
          </label>
          <DateInput
            day={day}
            month={month}
            year={year}
            onDayChange={(v) => { setDay(v); setError(""); }}
            onMonthChange={(v) => { setMonth(v); setError(""); }}
            onYearChange={(v) => { setYear(v); setError(""); }}
            error={error}
          />
        </div>

        {/* Birth hour */}
        <div>
          <label htmlFor="birth-hour" className="mono-label block mb-3">
            Gio sinh
          </label>
          <select
            id="birth-hour"
            value={hour}
            onChange={(e) => setHour(e.target.value)}
            className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg transition-colors cursor-pointer"
          >
            {BIRTH_HOURS.map((h) => (
              <option key={h.value} value={h.value}>
                {h.label}
              </option>
            ))}
          </select>
        </div>

        {/* Gender */}
        <fieldset>
          <legend className="mono-label mb-3">Gioi tinh</legend>
          <div className="flex gap-0" role="radiogroup">
            <button
              type="button"
              role="radio"
              aria-checked={gender === "nam"}
              onClick={() => setGender("nam")}
              className={`flex-1 py-3 text-xs uppercase tracking-widest border transition-colors ${
                gender === "nam"
                  ? "bg-fg text-bg border-fg"
                  : "bg-transparent text-fg-muted border-border"
              }`}
            >
              Nam
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={gender === "nu"}
              onClick={() => setGender("nu")}
              className={`flex-1 py-3 text-xs uppercase tracking-widest border border-l-0 transition-colors ${
                gender === "nu"
                  ? "bg-fg text-bg border-fg"
                  : "bg-transparent text-fg-muted border-border"
              }`}
            >
              Nu
            </button>
          </div>
        </fieldset>

        {/* Submit */}
        <button type="button" onClick={handleSubmit} className="btn-primary w-full">
          Xem ngay hom nay
        </button>
      </div>
    </div>
  );
}
