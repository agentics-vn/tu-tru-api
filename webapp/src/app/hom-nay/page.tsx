"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { mockTodayInfo, mockTuTruChart } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";
import { ScoreBadge } from "@/components/score-badge";

export default function HomNayPage() {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();
  const [showHours, setShowHours] = useState(false);

  const today = useMemo(() => mockTodayInfo(), []);
  const chart = useMemo(() => mockTuTruChart(), []);

  if (isLoaded && !profile) {
    router.replace("/");
    return null;
  }
  if (!isLoaded) return null;

  const now = new Date();
  const weekdays = [
    "Chu Nhat",
    "Thu Hai",
    "Thu Ba",
    "Thu Tu",
    "Thu Nam",
    "Thu Sau",
    "Thu Bay",
  ];

  return (
    <div className="px-6 py-6 page-enter">
      {/* Top bar */}
      <header className="flex justify-between items-start mb-10">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">
          {weekdays[now.getDay()]}
        </div>
      </header>

      {/* Date display */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="heading-display text-[3.5rem] leading-none">
            {String(now.getDate()).padStart(2, "0")}
          </h1>
          <div className="mono-label mt-1">
            Thang {now.getMonth() + 1}, {now.getFullYear()}
          </div>
        </div>
        <BracketText className="mt-1">
          <div className="flex flex-col items-center text-lg">
            <span>hom</span>
            <span>nay</span>
          </div>
        </BracketText>
      </div>

      {/* Lunar date */}
      <div className="mono-label mb-6">
        Am lich: {today.lunarDate} — {today.canChi}
      </div>

      {/* Hoang Dao badge + Score */}
      <div className="border-t border-b border-border py-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span
              className={`inline-block mono-label px-2 py-1 ${
                today.hoangDao
                  ? "bg-accent text-bg"
                  : "bg-bad text-bg"
              }`}
            >
              {today.hoangDao ? "Hoang Dao" : "Hac Dao"}
            </span>
            <span className="mono-label ml-2">Kim Quy</span>
          </div>
        </div>

        <ScoreBadge score={today.score} grade={today.grade} size="lg" />

        <div className="score-bar mt-4">
          <div
            className="score-bar-fill"
            style={{ width: `${today.score}%` }}
          />
        </div>
      </div>

      {/* Menh info */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div>
          <div className="mono-label mb-1">Menh</div>
          <div className="text-sm font-bold">{chart.menh}</div>
        </div>
        <div>
          <div className="mono-label mb-1">Nhat Chu</div>
          <div className="text-sm font-bold">{chart.nhatChu}</div>
        </div>
        <div>
          <div className="mono-label mb-1">Than</div>
          <div className="text-sm font-bold capitalize">
            {chart.cuongNhuoc}
          </div>
        </div>
      </div>

      {/* Nen lam / Nen tranh */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div>
          <div className="mono-label text-good mb-3">Nen lam</div>
          {today.goodFor.map((g) => (
            <div
              key={g}
              className="text-sm mb-2 pl-3 border-l-2 border-good"
            >
              {g}
            </div>
          ))}
        </div>
        <div>
          <div className="mono-label text-bad mb-3">Nen tranh</div>
          {today.badFor.map((b) => (
            <div
              key={b}
              className="text-sm mb-2 pl-3 border-l-2 border-bad"
            >
              {b}
            </div>
          ))}
        </div>
      </div>

      {/* Gio tot */}
      <div className="mb-8">
        <button
          onClick={() => setShowHours(!showHours)}
          className="mono-label flex items-center gap-2 mb-3 cursor-pointer"
        >
          Gio tot / xau
          <span className="text-[0.5rem]">{showHours ? "▲" : "▼"}</span>
        </button>
        {showHours && (
          <div className="flex flex-wrap gap-2 page-enter">
            {today.goodHours.map((h) => (
              <span
                key={h}
                className="mono-label px-3 py-2 bg-good/10 text-good border border-good/20"
              >
                {h}
              </span>
            ))}
            {today.badHours.map((h) => (
              <span
                key={h}
                className="mono-label px-3 py-2 bg-bad/10 text-bad border border-bad/20"
              >
                {h}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Insight */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="mono-label text-accent mb-2">Nhan dinh</div>
        <p className="text-sm leading-relaxed text-fg-muted">
          &ldquo;{today.reason}&rdquo;
        </p>
      </div>

      {/* CTAs */}
      <div className="space-y-3 mb-8">
        <button
          onClick={() => router.push("/chon-ngay")}
          className="btn-primary w-full"
        >
          Chon ngay tot cho viec lon
        </button>
        <button
          onClick={() => router.push("/toi")}
          className="btn-outline w-full"
        >
          Xem la so Tu Tru day du
        </button>
      </div>

      {/* Share */}
      <div className="text-center">
        <button className="mono-label text-accent">
          Chia se ngay hom nay
        </button>
      </div>
    </div>
  );
}
