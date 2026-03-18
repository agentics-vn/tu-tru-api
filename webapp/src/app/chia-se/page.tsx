"use client";

import { useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { mockTodayInfo, mockTuTruChart } from "@/lib/mock-data";

export default function ChiaSePage() {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();
  const cardRef = useRef<HTMLDivElement>(null);

  const today = useMemo(() => mockTodayInfo(), []);
  const chart = useMemo(() => mockTuTruChart(), []);

  if (isLoaded && !profile) {
    router.replace("/");
    return null;
  }
  if (!isLoaded) return null;

  const now = new Date();
  const dateStr = `${String(now.getDate()).padStart(2, "0")}/${String(now.getMonth() + 1).padStart(2, "0")}/${now.getFullYear()}`;

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: `Tu Tru — Ngay ${dateStr}`,
        text: `Ngay ${dateStr}: ${today.score}/100 diem — ${today.hoangDao ? "Hoang Dao" : "Hac Dao"}. Xem ngay cua ban tai Tu Tru!`,
        url: window.location.origin,
      });
    }
  };

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Chia se</div>
      </header>

      <h1 className="heading-display text-xl mb-2">Chia se ngay hom nay</h1>
      <p className="text-xs text-fg-muted mb-8">
        Card nay se duoc render thanh anh de chia se qua Zalo, Facebook, Instagram.
      </p>

      {/* Share Card Preview */}
      <div
        ref={cardRef}
        className="bg-bg-dark text-bg p-6 mb-8"
        style={{ aspectRatio: "9/16", maxHeight: "560px" }}
      >
        {/* Card content */}
        <div className="h-full flex flex-col justify-between">
          {/* Top */}
          <div className="flex justify-between items-start">
            <span
              className="text-[0.55rem] uppercase tracking-[0.2em] opacity-50"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              Tu Tru
            </span>
            <span
              className="text-[0.55rem] uppercase tracking-[0.2em] opacity-50"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {dateStr}
            </span>
          </div>

          {/* Center — date + score */}
          <div className="flex flex-col items-center text-center">
            {/* Bracket CJK */}
            <span className="text-accent text-xl leading-none mb-1">
              {"\u300C"}
            </span>
            <span className="text-accent text-xl tracking-widest">
              hom nay
            </span>
            <span className="text-accent text-xl leading-none mt-1">
              {"\u300D"}
            </span>

            <div
              className="text-[5rem] font-black leading-none mt-6 mb-2"
              style={{
                fontFamily: "var(--font-display)",
                letterSpacing: "-0.03em",
              }}
            >
              {today.score}
            </div>
            <div
              className="text-[0.55rem] uppercase tracking-[0.2em] opacity-50 mb-6"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              /100 — Hang {today.grade}
            </div>

            {/* Badge */}
            <span
              className="inline-block text-[0.55rem] uppercase tracking-[0.15em] px-3 py-1"
              style={{
                fontFamily: "var(--font-mono)",
                backgroundColor: "var(--accent)",
                color: "var(--bg-dark)",
              }}
            >
              {today.hoangDao ? "Hoang Dao" : "Hac Dao"}
            </span>
          </div>

          {/* Bottom — info grid */}
          <div>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center">
                <div
                  className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  Menh
                </div>
                <div className="text-xs font-bold">{chart.menh}</div>
              </div>
              <div className="text-center">
                <div
                  className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  Can Chi
                </div>
                <div className="text-xs font-bold">{today.canChi}</div>
              </div>
              <div className="text-center">
                <div
                  className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  Truc
                </div>
                <div className="text-xs font-bold">{today.trucName}</div>
              </div>
            </div>

            {/* Nen lam */}
            <div
              className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              Nen lam
            </div>
            <div className="text-xs opacity-70 mb-4">
              {today.goodFor.join(" — ")}
            </div>

            {/* QR placeholder */}
            <div className="flex items-center justify-between">
              <div
                className="text-[0.5rem] uppercase tracking-[0.15em] opacity-30"
                style={{ fontFamily: "var(--font-mono)" }}
              >
                Scan de xem ngay cua ban
              </div>
              <div className="w-10 h-10 border border-white/20 flex items-center justify-center">
                <span className="text-[0.45rem] opacity-30">QR</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <button onClick={handleShare} className="btn-primary w-full">
          Chia se
        </button>
        <button className="btn-outline w-full">
          Tai anh ve
        </button>
      </div>

      {/* Note */}
      <p className="mono-label text-center mt-6">
        Ban be scan qr → nhap ngay sinh → xem ngay cua ho
      </p>
    </div>
  );
}
