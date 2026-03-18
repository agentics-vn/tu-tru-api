"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireProfile } from "@/lib/use-require-profile";
import { mockTuTruChart, resetMockSeed } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";
import { useProfile } from "@/lib/profile-context";
import { HANH_COLORS } from "@/lib/utils";

const DAI_VAN = [
  { age: "3-12", can: "Canh", chi: "Thin" },
  { age: "13-22", can: "Tan", chi: "Ty" },
  { age: "23-32", can: "Nham", chi: "Ngo" },
  { age: "33-42", can: "Quy", chi: "Mui" },
  { age: "43-52", can: "Giap", chi: "Than" },
];

function getActiveVanIndex(birthYear: number): number {
  const age = new Date().getFullYear() - birthYear;
  return DAI_VAN.findIndex((dv) => {
    const [from, to] = dv.age.split("-").map(Number);
    return age >= from && age <= to;
  });
}

export default function ToiPage() {
  const { profile, isReady } = useRequireProfile();
  const { clearProfile } = useProfile();
  const router = useRouter();
  const [showDaiVan, setShowDaiVan] = useState(false);

  const chart = useMemo(() => {
    resetMockSeed(99);
    return mockTuTruChart();
  }, []);

  if (!isReady || !profile) return null;

  const birthYear = parseInt(profile.birthDate.split("-")[0]);
  const activeVanIdx = getActiveVanIndex(birthYear);
  const currentMonth = new Date().getMonth() + 1;
  const currentYear = new Date().getFullYear();

  const pillars = [
    { label: "Gio", ...chart.gio },
    { label: "Ngay", ...chart.ngay },
    { label: "Thang", ...chart.thang },
    { label: "Nam", ...chart.nam },
  ];

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Toi</div>
      </header>

      {/* Name + Birth */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="heading-display text-2xl mb-1">La so cua ban</h1>
          <div className="mono-label">
            {profile.birthDate} — {profile.gender === "nam" ? "Nam" : "Nu"}
          </div>
          <div className="mono-label mt-0.5">
            Gio sinh:{" "}
            {profile.birthHour === "unknown"
              ? "Khong ro"
              : profile.birthHour}
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
      <div className="border-t border-b border-border py-6 mb-6">
        <div className="mono-label mb-4 text-accent">La So Tu Tru</div>
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
                <div
                  className={`text-[0.6rem] ${HANH_COLORS[p.hanh] || "text-fg-muted"}`}
                >
                  {p.hanh}
                </div>
              </div>
              <div className="mono-label mt-2 text-[0.55rem] leading-tight">
                {p.napAm}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Core analysis */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div>
          <div className="mono-label mb-1">Nhat Chu</div>
          <div className="text-lg font-bold">{chart.nhatChu}</div>
        </div>
        <div>
          <div className="mono-label mb-1">Than</div>
          <div className="text-lg font-bold capitalize">
            La so {chart.cuongNhuoc}
          </div>
        </div>
        <div>
          <div className="mono-label mb-1">Menh</div>
          <div className="text-sm font-bold">{chart.menh}</div>
        </div>
        <div>
          <div className="mono-label mb-1">Dung Than</div>
          <div
            className={`text-sm font-bold ${HANH_COLORS[chart.dungThan]}`}
          >
            {chart.dungThan}
          </div>
        </div>
        <div>
          <div className="mono-label mb-1">Ky Than</div>
          <div
            className={`text-sm font-bold ${HANH_COLORS[chart.kyThan]}`}
          >
            {chart.kyThan}
          </div>
        </div>
      </div>

      {/* Tieu Van */}
      <div className="border-t border-border pt-5 mb-6">
        <div className="mono-label text-accent mb-3">
          Van thang {currentMonth}/{currentYear}
        </div>
        <div className="bg-bg-card p-4">
          <div className="text-sm font-bold mb-2">Canh Dan (Moc)</div>
          <p className="text-xs text-fg-muted leading-relaxed">
            &ldquo;Thang nay can dac biet can trong voi tai chinh. Moc khac
            menh Tho — nen tap trung giu suc khoe va han che rui
            ro.&rdquo;
          </p>
          <div className="flex gap-2 mt-3">
            <span className="mono-label px-2 py-0.5 border border-warn text-warn">
              Can trong
            </span>
            <span className="mono-label px-2 py-0.5 border border-border">
              Han che rui ro
            </span>
          </div>
        </div>
      </div>

      {/* Dai Van */}
      <div className="border-t border-border pt-5 mb-8">
        <button
          type="button"
          onClick={() => setShowDaiVan(!showDaiVan)}
          aria-expanded={showDaiVan}
          className="mono-label flex items-center gap-2 mb-4 cursor-pointer"
        >
          Dai Van (chu ky 10 nam)
          <span className="text-[0.5rem]">
            {showDaiVan ? "\u25B2" : "\u25BC"}
          </span>
        </button>

        {showDaiVan && (
          <div className="flex gap-0 page-enter">
            {DAI_VAN.map((dv, idx) => (
              <div
                key={dv.age}
                className={`flex-1 text-center py-3 border ${
                  idx === activeVanIdx
                    ? "bg-fg text-bg border-fg"
                    : "border-border"
                }`}
              >
                <div className="mono-label text-[0.5rem] mb-1">
                  {dv.age}
                </div>
                <div className="text-xs font-bold">{dv.can}</div>
                <div className="text-xs">{dv.chi}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Premium upsell */}
      <div className="border border-accent p-5 mb-8 text-center">
        <div className="mono-label text-accent mb-2">Premium</div>
        <h3 className="text-sm font-bold mb-2">
          AI Giai La So — Phan tich day du 2000+ tu
        </h3>
        <p className="text-xs text-fg-muted mb-4">
          Thay the tu van 20 trieu — chi 79K/thang
        </p>
        <button type="button" className="btn-primary px-8">
          Sap ra mat
        </button>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <button type="button" className="btn-outline w-full">
          Them nguoi than — sap ra mat
        </button>
        <button
          type="button"
          onClick={() => {
            clearProfile();
            router.replace("/");
          }}
          className="mono-label w-full py-3 text-center text-bad"
        >
          Xoa du lieu & bat dau lai
        </button>
      </div>
    </div>
  );
}
