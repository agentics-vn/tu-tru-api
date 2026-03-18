"use client";

import { useRequireProfile } from "@/lib/use-require-profile";
import { useApi } from "@/lib/use-api";
import { fetchNgayHomNay, fetchTuTru } from "@/lib/api";

export default function ChiaSePage() {
  const { profile, isReady } = useRequireProfile();

  const { data: today } = useApi(
    isReady && profile
      ? () => fetchNgayHomNay({ birthDate: profile.birthDate, birthHour: profile.birthHour, gender: profile.gender })
      : null,
    [profile?.birthDate]
  );

  const { data: chart } = useApi(
    isReady && profile
      ? () => fetchTuTru({ birthDate: profile.birthDate, birthHour: profile.birthHour, gender: profile.gender })
      : null,
    [profile?.birthDate]
  );

  if (!isReady) return null;

  const now = new Date();
  const dateStr = `${String(now.getDate()).padStart(2, "0")}/${String(now.getMonth() + 1).padStart(2, "0")}/${now.getFullYear()}`;

  const score = today
    ? (today.truc.score > 0 && today.hoang_dao.is_hoang_dao ? 82 : today.truc.score > 0 ? 65 : 50)
    : 0;
  const grade = score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : "D";

  const shareText = today
    ? `Ngay ${dateStr}: ${score}/100 diem — ${today.hoang_dao.is_hoang_dao ? "Hoang Dao" : "Hac Dao"}. Xem ngay cua ban tai Tu Tru!`
    : `Xem ngay tot xau tai Tu Tru!`;

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: `Tu Tru — Ngay ${dateStr}`,
          text: shareText,
          url: window.location.origin,
        });
      } else {
        await navigator.clipboard.writeText(shareText);
        alert("Da copy noi dung vao clipboard!");
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
    }
  };

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Chia se</div>
      </header>

      <h1 className="heading-display text-xl mb-2">Chia se ngay hom nay</h1>
      <p className="text-xs text-fg-muted mb-8">Card de chia se qua Zalo, Facebook, Instagram.</p>

      <div
        className="bg-bg-dark text-bg p-6 mb-8"
        style={{ aspectRatio: "9/16", maxHeight: "560px" }}
      >
        <div className="h-full flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-[0.55rem] uppercase tracking-[0.2em] opacity-50" style={{ fontFamily: "var(--font-mono)" }}>Tu Tru</span>
            <span className="text-[0.55rem] uppercase tracking-[0.2em] opacity-50" style={{ fontFamily: "var(--font-mono)" }}>{dateStr}</span>
          </div>

          <div className="flex flex-col items-center text-center">
            <span className="text-accent text-xl leading-none mb-1">{"\u300C"}</span>
            <span className="text-accent text-xl tracking-widest">hom nay</span>
            <span className="text-accent text-xl leading-none mt-1">{"\u300D"}</span>

            <div className="text-[5rem] font-black leading-none mt-6 mb-2" style={{ fontFamily: "var(--font-display)", letterSpacing: "-0.03em" }}>
              {score}
            </div>
            <div className="text-[0.55rem] uppercase tracking-[0.2em] opacity-50 mb-6" style={{ fontFamily: "var(--font-mono)" }}>
              /100 — Hang {grade}
            </div>

            {today && (
              <span
                className="inline-block text-[0.55rem] uppercase tracking-[0.15em] px-3 py-1"
                style={{ fontFamily: "var(--font-mono)", backgroundColor: "var(--accent)", color: "var(--bg-dark)" }}
              >
                {today.hoang_dao.is_hoang_dao ? "Hoang Dao" : "Hac Dao"}
              </span>
            )}
          </div>

          <div>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center">
                <div className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1" style={{ fontFamily: "var(--font-mono)" }}>Menh</div>
                <div className="text-xs font-bold">{chart?.menh.nap_am_name || "—"}</div>
              </div>
              <div className="text-center">
                <div className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1" style={{ fontFamily: "var(--font-mono)" }}>Can Chi</div>
                <div className="text-xs font-bold">{today?.can_chi.name || "—"}</div>
              </div>
              <div className="text-center">
                <div className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1" style={{ fontFamily: "var(--font-mono)" }}>Truc</div>
                <div className="text-xs font-bold">{today?.truc.name || "—"}</div>
              </div>
            </div>

            <div className="text-[0.5rem] uppercase tracking-[0.15em] opacity-40 mb-1" style={{ fontFamily: "var(--font-mono)" }}>Nen lam</div>
            <div className="text-xs opacity-70 mb-4">
              {today?.good_for.join(" — ") || "—"}
            </div>

            <div className="flex items-center justify-between">
              <div className="text-[0.5rem] uppercase tracking-[0.15em] opacity-30" style={{ fontFamily: "var(--font-mono)" }}>
                tutru.app — Xem ngay cua ban
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <button type="button" onClick={handleShare} className="btn-primary w-full">Chia se</button>
      </div>

      <p className="mono-label text-center mt-6">Ban be truy cap tutru.app → nhap ngay sinh → xem ngay cua ho</p>
    </div>
  );
}
