"use client";

import { useState } from "react";
import Link from "next/link";
import { useRequireProfile } from "@/lib/use-require-profile";
import { useApi } from "@/lib/use-api";
import { fetchNgayHomNay, fetchTuTru } from "@/lib/api";
import { BracketText } from "@/components/bracket-text";
import { ScoreBadge } from "@/components/score-badge";

export default function HomNayPage() {
  const { profile, isReady } = useRequireProfile();
  const [showHours, setShowHours] = useState(false);

  const { data: today, loading: loadingToday, error: errorToday } = useApi(
    isReady && profile
      ? () =>
          fetchNgayHomNay({
            birthDate: profile.birthDate,
            birthHour: profile.birthHour,
            gender: profile.gender,
          })
      : null,
    [profile?.birthDate]
  );

  const { data: chart } = useApi(
    isReady && profile
      ? () =>
          fetchTuTru({
            birthDate: profile.birthDate,
            birthHour: profile.birthHour,
            gender: profile.gender,
          })
      : null,
    [profile?.birthDate]
  );

  if (!isReady || !profile) return null;

  const now = new Date();
  const weekdays = [
    "Chu Nhat", "Thu Hai", "Thu Ba", "Thu Tu", "Thu Nam", "Thu Sau", "Thu Bay",
  ];

  if (loadingToday) {
    return (
      <div className="px-6 py-6">
        <header className="flex justify-between items-start mb-10">
          <div className="mono-label">Tu Tru</div>
          <div className="mono-label">{weekdays[now.getDay()]}</div>
        </header>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="mono-label text-accent">Dang tai du lieu...</div>
        </div>
      </div>
    );
  }

  if (errorToday) {
    return (
      <div className="px-6 py-6">
        <header className="flex justify-between items-start mb-10">
          <div className="mono-label">Tu Tru</div>
          <div className="mono-label">{weekdays[now.getDay()]}</div>
        </header>
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <div className="mono-label text-bad">Khong the tai du lieu</div>
          <p className="text-xs text-fg-muted text-center max-w-[260px]">{errorToday}</p>
        </div>
      </div>
    );
  }

  if (!today) return null;

  const score = today.bat_tu ? 80 : (today.truc.score > 0 && today.hoang_dao.is_hoang_dao ? 82 : today.truc.score > 0 ? 65 : 50);
  const grade = score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : "D";

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-10">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">{weekdays[now.getDay()]}</div>
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
        {today.lunar.display} — {today.can_chi.name}
      </div>

      {/* Hoang Dao badge + Score */}
      <div className="border-t border-b border-border py-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span
              className={`inline-block mono-label px-2 py-1 ${
                today.hoang_dao.is_hoang_dao ? "bg-accent text-bg" : "bg-bad text-bg"
              }`}
            >
              {today.hoang_dao.badge}
            </span>
            <span className="mono-label ml-2">{today.hoang_dao.star_name}</span>
          </div>
        </div>

        <ScoreBadge score={score} grade={grade as "A"|"B"|"C"|"D"} size="lg" />

        <div className="score-bar mt-4">
          <div className="score-bar-fill" style={{ width: `${score}%` }} />
        </div>
      </div>

      {/* Menh info */}
      {chart && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div>
            <div className="mono-label mb-1">Menh</div>
            <div className="text-sm font-bold">{chart.menh.nap_am_name}</div>
          </div>
          <div>
            <div className="mono-label mb-1">Nhat Chu</div>
            <div className="text-sm font-bold">
              {chart.nhat_chu ? `${chart.nhat_chu.can_name} ${chart.nhat_chu.hanh}` : chart.menh.hanh}
            </div>
          </div>
          <div>
            <div className="mono-label mb-1">Than</div>
            <div className="text-sm font-bold capitalize">
              {chart.chart_strength === "weak" ? "Nhuoc" : chart.chart_strength === "strong" ? "Vuong" : chart.menh.hanh}
            </div>
          </div>
        </div>
      )}

      {/* Nen lam / Nen tranh */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div>
          <div className="mono-label text-good mb-3">Nen lam</div>
          {today.good_for.map((g) => (
            <div key={g} className="text-sm mb-2 pl-3 border-l-2 border-good">{g}</div>
          ))}
          {today.good_for.length === 0 && (
            <div className="text-xs text-fg-muted">Khong co goi y dac biet</div>
          )}
        </div>
        <div>
          <div className="mono-label text-bad mb-3">Nen tranh</div>
          {today.avoid_for.map((b) => (
            <div key={b} className="text-sm mb-2 pl-3 border-l-2 border-bad">{b}</div>
          ))}
          {today.avoid_for.length === 0 && (
            <div className="text-xs text-fg-muted">Khong co gi dac biet</div>
          )}
        </div>
      </div>

      {/* Gio tot */}
      <div className="mb-8">
        <button
          type="button"
          onClick={() => setShowHours(!showHours)}
          aria-expanded={showHours}
          className="mono-label flex items-center gap-2 mb-3 cursor-pointer"
        >
          Gio tot / xau
          <span className="text-[0.5rem]">{showHours ? "\u25B2" : "\u25BC"}</span>
        </button>
        {showHours && (
          <div className="flex flex-wrap gap-2 page-enter">
            {today.gio_tot.map((h) => (
              <span key={h.chi_name} className="mono-label px-3 py-2 bg-good/10 text-good border border-good/20">
                {h.chi_name} ({h.range})
              </span>
            ))}
            {today.gio_xau.map((h) => (
              <span key={h.chi_name} className="mono-label px-3 py-2 bg-bad/10 text-bad border border-bad/20">
                {h.chi_name} ({h.range})
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Insight */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="mono-label text-accent mb-2">Nhan dinh</div>
        <p className="text-sm leading-relaxed text-fg-muted">
          {today.daily_advice.nen_lam}
        </p>
        {today.daily_advice.nen_tranh && today.daily_advice.nen_tranh !== "Không có gì đặc biệt." && (
          <p className="text-sm leading-relaxed text-bad mt-2">
            {today.daily_advice.nen_tranh}
          </p>
        )}
      </div>

      {/* CTAs */}
      <div className="space-y-3 mb-8">
        <Link href="/chon-ngay" className="btn-primary w-full block text-center">
          Chon ngay tot cho viec lon
        </Link>
        <Link href="/toi" className="btn-outline w-full block text-center">
          Xem la so Tu Tru day du
        </Link>
      </div>

      {/* Quick links */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="mono-label mb-3">Kham pha them</div>
        <div className="grid grid-cols-2 gap-2">
          {[
            { href: "/hop-tuoi", label: "Hop tuoi doi lua" },
            { href: "/phong-thuy", label: "Phong thuy ca nhan" },
            { href: "/so-sanh", label: "So sanh 2 ngay" },
            { href: "/su-kien", label: "Su kien cua ban" },
          ].map((link) => (
            <Link key={link.href} href={link.href} className="text-left py-3 px-3 border border-border text-xs transition-colors hover:border-fg">
              {link.label}
            </Link>
          ))}
        </div>
      </div>

      <div className="text-center">
        <Link href="/chia-se" className="mono-label text-accent">Chia se ngay hom nay</Link>
      </div>
    </div>
  );
}
