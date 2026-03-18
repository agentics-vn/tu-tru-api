"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireProfile } from "@/lib/use-require-profile";
import { useApi } from "@/lib/use-api";
import { fetchTuTru, fetchTieuVan } from "@/lib/api";
import { BracketText } from "@/components/bracket-text";
import { useProfile } from "@/lib/profile-context";
import { HANH_COLORS } from "@/lib/utils";

export default function ToiPage() {
  const { profile, isReady } = useRequireProfile();
  const { clearProfile } = useProfile();
  const router = useRouter();
  const [showDaiVan, setShowDaiVan] = useState(false);

  const currentMonth = new Date().getMonth() + 1;
  const currentYear = new Date().getFullYear();
  const monthStr = `${currentYear}-${String(currentMonth).padStart(2, "0")}`;

  const { data: chart, loading: chartLoading } = useApi(
    isReady && profile
      ? () => fetchTuTru({ birthDate: profile.birthDate, birthHour: profile.birthHour, gender: profile.gender })
      : null,
    [profile?.birthDate]
  );

  const { data: tieuVan } = useApi(
    isReady && profile
      ? () => fetchTieuVan({ birthDate: profile.birthDate, birthHour: profile.birthHour, gender: profile.gender, month: monthStr })
      : null,
    [profile?.birthDate, monthStr]
  );

  if (!isReady || !profile) return null;

  if (chartLoading) {
    return (
      <div className="px-6 py-6">
        <header className="flex justify-between items-start mb-8">
          <div className="mono-label">Tu Tru</div>
          <div className="mono-label">Toi</div>
        </header>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="mono-label text-accent">Dang tai la so...</div>
        </div>
      </div>
    );
  }

  const birthYear = parseInt(profile.birthDate.split("-")[0]);

  // Build pillars from API data
  const pillars = chart?.pillars
    ? [
        { label: "Gio", can: chart.pillars.hour.can.name, chi: chart.pillars.hour.chi.name, napAm: chart.pillars.hour.nap_am.name, hanh: chart.pillars.hour.nap_am.hanh },
        { label: "Ngay", can: chart.pillars.day.can.name, chi: chart.pillars.day.chi.name, napAm: chart.pillars.day.nap_am.name, hanh: chart.pillars.day.nap_am.hanh },
        { label: "Thang", can: chart.pillars.month.can.name, chi: chart.pillars.month.chi.name, napAm: chart.pillars.month.nap_am.name, hanh: chart.pillars.month.nap_am.hanh },
        { label: "Nam", can: chart.pillars.year.can.name, chi: chart.pillars.year.chi.name, napAm: chart.pillars.year.nap_am.name, hanh: chart.pillars.year.nap_am.hanh },
      ]
    : null;

  // Active Đại Vận
  const age = currentYear - birthYear;
  const activeVanIdx = chart?.dai_van?.cycles.findIndex((c) => {
    const [from, to] = c.age_range.split("-").map(Number);
    return age >= from && age <= to;
  }) ?? -1;

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Toi</div>
      </header>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="heading-display text-2xl mb-1">La so cua ban</h1>
          <div className="mono-label">
            {profile.birthDate} — {profile.gender === "nam" ? "Nam" : "Nu"}
          </div>
          <div className="mono-label mt-0.5">
            Gio sinh: {profile.birthHour === "unknown" ? "Khong ro" : profile.birthHour}
          </div>
        </div>
        <BracketText>
          <div className="flex flex-col items-center text-base">
            <span>la</span>
            <span>so</span>
          </div>
        </BracketText>
      </div>

      {/* Tu Tru Chart */}
      {pillars && (
        <div className="border-t border-b border-border py-6 mb-6">
          <div className="mono-label mb-4 text-accent">
            La So Tu Tru {chart?.tu_tru_display ? `— ${chart.tu_tru_display}` : ""}
          </div>
          <div className="grid grid-cols-4 gap-0">
            {pillars.map((p) => (
              <div key={p.label} className="text-center">
                <div className="mono-label mb-3">{p.label}</div>
                <div className="border border-border py-3 mb-0">
                  <div className="text-sm font-bold">{p.can}</div>
                </div>
                <div className="border border-border border-t-0 py-3 mb-0">
                  <div className="text-sm font-bold">{p.chi}</div>
                </div>
                <div className="border border-border border-t-0 py-3">
                  <div className={`text-[0.6rem] ${HANH_COLORS[p.hanh] || "text-fg-muted"}`}>{p.hanh}</div>
                </div>
                <div className="mono-label mt-2 text-[0.55rem] leading-tight">{p.napAm}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Core analysis */}
      {chart && (
        <div className="grid grid-cols-2 gap-6 mb-8">
          <div>
            <div className="mono-label mb-1">Nhat Chu</div>
            <div className="text-lg font-bold">
              {chart.nhat_chu ? `${chart.nhat_chu.can_name} ${chart.nhat_chu.hanh}` : chart.menh.hanh}
            </div>
          </div>
          <div>
            <div className="mono-label mb-1">Than</div>
            <div className="text-lg font-bold capitalize">
              La so {chart.chart_strength === "weak" ? "nhuoc" : chart.chart_strength === "strong" ? "vuong" : "—"}
            </div>
          </div>
          <div>
            <div className="mono-label mb-1">Menh</div>
            <div className="text-sm font-bold">{chart.menh.nap_am_name}</div>
          </div>
          <div>
            <div className="mono-label mb-1">Dung Than</div>
            <div className={`text-sm font-bold ${HANH_COLORS[chart.dung_than?.element || ""] || ""}`}>
              {chart.dung_than?.element || chart.menh.duong_than}
            </div>
          </div>
          <div>
            <div className="mono-label mb-1">Ky Than</div>
            <div className={`text-sm font-bold ${HANH_COLORS[chart.ky_than?.element || ""] || ""}`}>
              {chart.ky_than?.element || chart.menh.ky_than}
            </div>
          </div>
        </div>
      )}

      {/* Thap Than */}
      {chart?.thap_than && (
        <div className="border-t border-border pt-5 mb-6">
          <div className="mono-label text-accent mb-3">Thap Than</div>
          <div className="grid grid-cols-3 gap-3">
            {chart.thap_than.year && (
              <div className="bg-bg-card p-3 text-center">
                <div className="mono-label mb-1">Nam</div>
                <div className="text-xs font-bold">{chart.thap_than.year.name}</div>
              </div>
            )}
            {chart.thap_than.month && (
              <div className="bg-bg-card p-3 text-center">
                <div className="mono-label mb-1">Thang</div>
                <div className="text-xs font-bold">{chart.thap_than.month.name}</div>
              </div>
            )}
            {chart.thap_than.hour && (
              <div className="bg-bg-card p-3 text-center">
                <div className="mono-label mb-1">Gio</div>
                <div className="text-xs font-bold">{chart.thap_than.hour.name}</div>
              </div>
            )}
          </div>
          {chart.thap_than.dominant && (
            <div className="mono-label mt-2">
              Chu dao: {chart.thap_than.dominant.name}
            </div>
          )}
        </div>
      )}

      {/* Tieu Van */}
      <div className="border-t border-border pt-5 mb-6">
        <div className="mono-label text-accent mb-3">Van thang {currentMonth}/{currentYear}</div>
        {tieuVan ? (
          <div className="bg-bg-card p-4">
            <div className="text-sm font-bold mb-2">
              {tieuVan.tieu_van_pillar.display} ({tieuVan.tieu_van_pillar.nap_am_hanh})
            </div>
            <p className="text-xs text-fg-muted leading-relaxed">
              &ldquo;{tieuVan.reading}&rdquo;
            </p>
            {tieuVan.tags.length > 0 && (
              <div className="flex gap-2 mt-3">
                {tieuVan.tags.map((tag) => (
                  <span key={tag} className="mono-label px-2 py-0.5 border border-border">{tag}</span>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="mono-label text-fg-muted">Dang tai...</div>
        )}
      </div>

      {/* Dai Van */}
      {chart?.dai_van && (
        <div className="border-t border-border pt-5 mb-8">
          <button
            type="button"
            onClick={() => setShowDaiVan(!showDaiVan)}
            aria-expanded={showDaiVan}
            className="mono-label flex items-center gap-2 mb-4 cursor-pointer"
          >
            Dai Van (chu ky 10 nam)
            <span className="text-[0.5rem]">{showDaiVan ? "\u25B2" : "\u25BC"}</span>
          </button>

          {showDaiVan && (
            <div className="flex gap-0 page-enter overflow-x-auto">
              {chart.dai_van.cycles.map((dv, idx) => (
                <div
                  key={dv.age_range}
                  className={`flex-1 min-w-[60px] text-center py-3 border ${
                    idx === activeVanIdx ? "bg-fg text-bg border-fg" : "border-border"
                  }`}
                >
                  <div className="mono-label text-[0.5rem] mb-1">{dv.age_range}</div>
                  <div className="text-xs font-bold">{dv.display}</div>
                  <div className={`text-[0.5rem] ${HANH_COLORS[dv.hanh] || ""}`}>{dv.hanh}</div>
                </div>
              ))}
            </div>
          )}

          {chart.dai_van.current && (
            <div className="mono-label mt-3">
              Hien tai: {chart.dai_van.current.display} ({chart.dai_van.current.age_range} tuoi)
            </div>
          )}
        </div>
      )}

      {/* Premium upsell */}
      <div className="border border-accent p-5 mb-8 text-center">
        <div className="mono-label text-accent mb-2">Premium</div>
        <h3 className="text-sm font-bold mb-2">AI Giai La So — Phan tich day du 2000+ tu</h3>
        <p className="text-xs text-fg-muted mb-4">Thay the tu van 20 trieu — chi 79K/thang</p>
        <button type="button" className="btn-primary px-8">Sap ra mat</button>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <button type="button" className="btn-outline w-full">Them nguoi than — sap ra mat</button>
        <button
          type="button"
          onClick={() => { clearProfile(); router.replace("/"); }}
          className="mono-label w-full py-3 text-center text-bad"
        >
          Xoa du lieu & bat dau lai
        </button>
      </div>
    </div>
  );
}
