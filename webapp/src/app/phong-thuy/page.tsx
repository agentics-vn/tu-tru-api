"use client";

import { useRequireProfile } from "@/lib/use-require-profile";
import { useApi } from "@/lib/use-api";
import { fetchPhongThuy } from "@/lib/api";
import { BracketText } from "@/components/bracket-text";
import { HANH_COLORS } from "@/lib/utils";

export default function PhongThuyPage() {
  const { profile, isReady } = useRequireProfile();

  const { data, loading, error } = useApi(
    isReady && profile
      ? () =>
          fetchPhongThuy({
            birthDate: profile.birthDate,
            birthHour: profile.birthHour,
            gender: profile.gender,
          })
      : null,
    [profile?.birthDate]
  );

  if (!isReady || !profile) return null;

  if (loading) {
    return (
      <div className="px-6 py-6">
        <header className="flex justify-between items-start mb-8">
          <div className="mono-label">Tu Tru</div>
          <div className="mono-label">Phong thuy</div>
        </header>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="mono-label text-accent">Dang tai...</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="px-6 py-6">
        <header className="flex justify-between items-start mb-8">
          <div className="mono-label">Tu Tru</div>
          <div className="mono-label">Phong thuy</div>
        </header>
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-2">
          <div className="mono-label text-bad">Loi tai du lieu</div>
          {error && <p className="text-xs text-fg-muted">{error}</p>}
        </div>
      </div>
    );
  }

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
          <div className={`text-2xl font-bold ${HANH_COLORS[data.dung_than] || ""}`}>{data.dung_than}</div>
          <div className="mono-label mt-1">Tang cuong hanh nay</div>
        </div>
        <div className="border border-bad p-4">
          <div className="mono-label text-bad mb-1">Ky Than</div>
          <div className={`text-2xl font-bold ${HANH_COLORS[data.ky_than] || ""}`}>{data.ky_than}</div>
          <div className="mono-label mt-1">Tranh hanh nay</div>
        </div>
      </div>

      {/* Huong tot */}
      <div className="border-t border-border pt-5 mb-6">
        <div className="mono-label text-good mb-4">Huong tot</div>
        {data.huong_tot.map((h) => (
          <div key={h.direction} className="flex items-start gap-3 mb-3 pl-3 border-l-2 border-good">
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
        {data.huong_xau.map((h) => (
          <div key={h.direction} className="flex items-start gap-3 mb-3 pl-3 border-l-2 border-bad">
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
          {data.mau_may_man.map((m) => (
            <div key={m.color} className="flex-1 text-center">
              <div className="w-full aspect-square mb-2" style={{ backgroundColor: m.hex }} role="img" aria-label={`Mau ${m.color}`} />
              <div className="text-xs font-bold">{m.color}</div>
              <div className="mono-label">{m.element}</div>
            </div>
          ))}
        </div>

        <div className="mono-label text-bad mb-3 mt-6">Mau nen tranh</div>
        <div className="flex gap-3">
          {data.mau_ky.map((m) => (
            <div key={m.color} className="flex-1 text-center">
              <div className="w-full aspect-square mb-2 opacity-50" style={{ backgroundColor: m.hex }} role="img" aria-label={`Mau ${m.color}`} />
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
              {data.so_may_man.map((s, i) => (
                <span key={`good-${i}`} className="w-10 h-10 flex items-center justify-center border border-good text-good font-bold">{s}</span>
              ))}
            </div>
          </div>
          <div>
            <div className="mono-label text-bad mb-3">So nen tranh</div>
            <div className="flex gap-2">
              {data.so_ky.map((s, i) => (
                <span key={`bad-${i}`} className="w-10 h-10 flex items-center justify-center border border-bad text-bad font-bold">{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Vat pham */}
      <div className="border-t border-border pt-5 mb-8">
        <div className="mono-label text-accent mb-4">Vat pham phong thuy</div>
        {data.vat_pham.map((v) => (
          <div key={v.item} className="bg-bg-card p-3 mb-2">
            <div className="flex justify-between items-start mb-1">
              <div className="text-sm font-bold">{v.item}</div>
              <span className={`mono-label ${HANH_COLORS[v.element] || ""}`}>{v.element}</span>
            </div>
            <p className="text-xs text-fg-muted">{v.reason}</p>
          </div>
        ))}
      </div>

      <div className="border border-accent p-5 text-center">
        <div className="mono-label text-accent mb-2">Premium</div>
        <h3 className="text-sm font-bold mb-2">Phan tich phong thuy chi tiet cho nha / van phong</h3>
        <button type="button" className="btn-primary px-8 mt-2">Sap ra mat</button>
      </div>
    </div>
  );
}
