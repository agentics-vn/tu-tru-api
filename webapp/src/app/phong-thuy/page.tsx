"use client";

import { useMemo } from "react";
import { useRequireProfile } from "@/lib/use-require-profile";
import { mockPhongThuyResult, resetMockSeed } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";
import { HANH_COLORS } from "@/lib/utils";

export default function PhongThuyPage() {
  const { profile, isReady } = useRequireProfile();

  const data = useMemo(() => {
    resetMockSeed(77);
    return mockPhongThuyResult();
  }, []);

  if (!isReady || !profile) return null;

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Phong thuy</div>
      </header>

      <div className="flex items-start justify-between mb-10">
        <div>
          <h1 className="heading-display text-[2rem] leading-tight">
            Phong thuy
            <br />
            ca nhan
          </h1>
          <p className="text-xs text-fg-muted mt-2 max-w-[240px] leading-relaxed">
            Huong nha, mau sac, so may man — tat ca dua tren Dung Than cua
            rieng ban.
          </p>
        </div>
        <BracketText className="mt-1">
          <div className="flex flex-col items-center text-base">
            <span>phong</span>
            <span>thuy</span>
          </div>
        </BracketText>
      </div>

      {/* Dung Than / Ky Than */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="border border-good p-4">
          <div className="mono-label text-good mb-1">Dung Than</div>
          <div className={`text-2xl font-bold ${HANH_COLORS[data.dungThan]}`}>
            {data.dungThan}
          </div>
          <div className="mono-label mt-1">Tang cuong hanh nay</div>
        </div>
        <div className="border border-bad p-4">
          <div className="mono-label text-bad mb-1">Ky Than</div>
          <div className={`text-2xl font-bold ${HANH_COLORS[data.kyThan]}`}>
            {data.kyThan}
          </div>
          <div className="mono-label mt-1">Tranh hanh nay</div>
        </div>
      </div>

      {/* Huong tot */}
      <div className="border-t border-border pt-5 mb-6">
        <div className="mono-label text-good mb-4">Huong tot</div>
        {data.huongTot.map((h) => (
          <div
            key={h.direction}
            className="flex items-start gap-3 mb-3 pl-3 border-l-2 border-good"
          >
            <div>
              <div className="text-sm font-bold">{h.direction}</div>
              <div className="mono-label">{h.element}</div>
              <p className="text-xs text-fg-muted mt-0.5">{h.reason}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Huong xau */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="mono-label text-bad mb-4">Huong xau</div>
        {data.huongXau.map((h) => (
          <div
            key={h.direction}
            className="flex items-start gap-3 mb-3 pl-3 border-l-2 border-bad"
          >
            <div>
              <div className="text-sm font-bold">{h.direction}</div>
              <div className="mono-label">{h.element}</div>
              <p className="text-xs text-fg-muted mt-0.5">{h.reason}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Mau sac */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="mono-label text-accent mb-4">Mau may man</div>
        <div className="flex gap-3 mb-4">
          {data.mauMayMan.map((m) => (
            <div key={m.color} className="flex-1 text-center">
              <div
                className="w-full aspect-square mb-2"
                style={{ backgroundColor: m.hex }}
                role="img"
                aria-label={`Mau ${m.color}`}
              />
              <div className="text-xs font-bold">{m.color}</div>
              <div className="mono-label">{m.element}</div>
            </div>
          ))}
        </div>

        <div className="mono-label text-bad mb-3 mt-6">Mau nen tranh</div>
        <div className="flex gap-3">
          {data.mauKy.map((m) => (
            <div key={m.color} className="flex-1 text-center">
              <div
                className="w-full aspect-square mb-2 opacity-50"
                style={{ backgroundColor: m.hex }}
                role="img"
                aria-label={`Mau ${m.color}`}
              />
              <div className="text-xs font-bold">{m.color}</div>
              <div className="mono-label">{m.element}</div>
            </div>
          ))}
        </div>
      </div>

      {/* So may man */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="mono-label text-good mb-3">So may man</div>
            <div className="flex gap-2">
              {data.soMayMan.map((s, i) => (
                <span
                  key={`good-${i}`}
                  className="w-10 h-10 flex items-center justify-center border border-good text-good font-bold"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div>
            <div className="mono-label text-bad mb-3">So nen tranh</div>
            <div className="flex gap-2">
              {data.soKy.map((s, i) => (
                <span
                  key={`bad-${i}`}
                  className="w-10 h-10 flex items-center justify-center border border-bad text-bad font-bold"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Vat pham */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="mono-label text-accent mb-4">Vat pham phong thuy</div>
        {data.vatPham.map((v) => (
          <div key={v.item} className="bg-bg-card p-3 mb-2">
            <div className="flex justify-between items-start mb-1">
              <div className="text-sm font-bold">{v.item}</div>
              <span className={`mono-label ${HANH_COLORS[v.element]}`}>
                {v.element}
              </span>
            </div>
            <p className="text-xs text-fg-muted">{v.reason}</p>
          </div>
        ))}
      </div>

      {/* Premium upsell */}
      <div className="border border-accent p-5 text-center">
        <div className="mono-label text-accent mb-2">Premium</div>
        <h3 className="text-sm font-bold mb-2">
          Phan tich phong thuy chi tiet cho nha / van phong
        </h3>
        <button type="button" className="btn-primary px-8 mt-2">
          Sap ra mat
        </button>
      </div>
    </div>
  );
}
