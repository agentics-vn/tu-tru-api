"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { BIRTH_HOURS } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";

export default function LandingPage() {
  const router = useRouter();
  const { profile, setProfile, isLoaded } = useProfile();

  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [hour, setHour] = useState("unknown");
  const [gender, setGender] = useState<"nam" | "nu">("nam");

  // If already has profile, redirect
  if (isLoaded && profile) {
    router.replace("/hom-nay");
    return null;
  }

  if (!isLoaded) return null;

  const handleSubmit = () => {
    const d = parseInt(day);
    const m = parseInt(month);
    const y = parseInt(year);
    if (!d || !m || !y || y < 1920 || y > 2020 || m < 1 || m > 12 || d < 1 || d > 31) return;

    const birthDate = `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    setProfile({ birthDate, birthHour: hour, gender });
    router.push("/hom-nay");
  };

  return (
    <div className="min-h-dvh flex flex-col justify-between px-6 py-8 page-enter">
      {/* Header */}
      <header className="flex justify-between items-start">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">[2026]</div>
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
          <label className="mono-label block mb-3">Ngay sinh</label>
          <div className="flex gap-3">
            <input
              type="text"
              inputMode="numeric"
              maxLength={2}
              placeholder="DD"
              value={day}
              onChange={(e) => setDay(e.target.value.replace(/\D/g, ""))}
              className="flex-1 bg-transparent border-b border-border py-3 text-center text-lg font-bold focus:outline-none focus:border-fg transition-colors placeholder:text-border"
            />
            <span className="text-border self-end pb-3">/</span>
            <input
              type="text"
              inputMode="numeric"
              maxLength={2}
              placeholder="MM"
              value={month}
              onChange={(e) => setMonth(e.target.value.replace(/\D/g, ""))}
              className="flex-1 bg-transparent border-b border-border py-3 text-center text-lg font-bold focus:outline-none focus:border-fg transition-colors placeholder:text-border"
            />
            <span className="text-border self-end pb-3">/</span>
            <input
              type="text"
              inputMode="numeric"
              maxLength={4}
              placeholder="YYYY"
              value={year}
              onChange={(e) => setYear(e.target.value.replace(/\D/g, ""))}
              className="flex-[1.5] bg-transparent border-b border-border py-3 text-center text-lg font-bold focus:outline-none focus:border-fg transition-colors placeholder:text-border"
            />
          </div>
        </div>

        {/* Birth hour */}
        <div>
          <label className="mono-label block mb-3">Gio sinh</label>
          <select
            value={hour}
            onChange={(e) => setHour(e.target.value)}
            className="w-full bg-transparent border-b border-border py-3 text-sm focus:outline-none focus:border-fg transition-colors appearance-none cursor-pointer"
          >
            {BIRTH_HOURS.map((h) => (
              <option key={h.value} value={h.value}>
                {h.label}
              </option>
            ))}
          </select>
        </div>

        {/* Gender */}
        <div>
          <label className="mono-label block mb-3">Gioi tinh</label>
          <div className="flex gap-0">
            <button
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
        </div>

        {/* Submit */}
        <button onClick={handleSubmit} className="btn-primary w-full">
          Xem ngay hom nay
        </button>

        {/* Social proof */}
        <p className="mono-label text-center">
          47,832 nguoi da xem hom nay
        </p>
      </div>
    </div>
  );
}
