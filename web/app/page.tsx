"use client";

import { useState } from "react";
import { fetchLaSoFull } from "@/lib/api";
import type { MenhBanPayload } from "@/lib/types";
import { MenhBanTuTru } from "@/components/MenhBanTuTru";

const BIRTH_TIMES = [
  { value: 0, label: "Tý Sớm (0h)" },
  { value: 2, label: "Sửu (1-2h)" },
  { value: 4, label: "Dần (3-4h)" },
  { value: 6, label: "Mão (5-6h)" },
  { value: 8, label: "Thìn (7-8h)" },
  { value: 10, label: "Tỵ (9-10h)" },
  { value: 11, label: "Ngọ (11-12h)" },
  { value: 14, label: "Mùi (13-14h)" },
  { value: 16, label: "Thân (15-16h)" },
  { value: 18, label: "Dậu (17-18h)" },
  { value: 20, label: "Tuất (19-20h)" },
  { value: 22, label: "Hợi (21-22h)" },
  { value: 23, label: "Tý Muộn (23h)" },
];

export default function HomePage() {
  const [name, setName] = useState("");
  const [birthDate, setBirthDate] = useState("1990-01-15");
  const [birthTime, setBirthTime] = useState(10);
  const [gender, setGender] = useState(1);
  const [viewYear, setViewYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chart, setChart] = useState<MenhBanPayload | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // The date input yields YYYY-MM-DD; the API expects dd/mm/yyyy.
      const [y, m, d] = birthDate.split("-");
      const res = await fetchLaSoFull({
        name: name || undefined,
        birth_date: `${d}/${m}/${y}`,
        birth_time: birthTime,
        gender,
        view_year: viewYear,
      });
      setChart(res.menh_ban);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi không xác định");
    } finally {
      setLoading(false);
    }
  }

  const inputCls =
    "rounded border border-hairline bg-paper px-2 py-1.5 text-ink outline-none focus:border-gold";

  return (
    <main className="pb-12">
      <div className="border-b border-gold/30 bg-forest-deep px-4 py-4 text-center">
        <p className="font-display text-xs uppercase tracking-[0.4em] text-gold">
          Luangiaibattu.vn
        </p>
        <h1 className="mt-1 font-display text-2xl font-bold tracking-wide text-gold-light">
          Lá Số Bát Tự — Mệnh Bàn Tứ Trụ
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="mx-auto mt-6 flex max-w-4xl flex-wrap items-end gap-3 rounded-lg border border-gold/40 bg-paper p-4 shadow-lg"
      >
        <label className="flex min-w-[140px] flex-1 flex-col gap-1 font-display text-sm uppercase tracking-wide text-muted">
          Họ tên
          <input
            className={inputCls}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label className="flex min-w-[140px] flex-1 flex-col gap-1 font-display text-sm uppercase tracking-wide text-muted">
          Ngày sinh
          <input
            type="date"
            required
            className={inputCls}
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
          />
        </label>
        <label className="flex min-w-[120px] flex-1 flex-col gap-1 font-display text-sm uppercase tracking-wide text-muted">
          Giờ
          <select
            className={inputCls}
            value={birthTime}
            onChange={(e) => setBirthTime(Number(e.target.value))}
          >
            {BIRTH_TIMES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex w-24 flex-col gap-1 font-display text-sm uppercase tracking-wide text-muted">
          Năm xem
          <input
            type="number"
            min={1900}
            max={2200}
            className={inputCls}
            value={viewYear}
            onChange={(e) => setViewYear(Number(e.target.value))}
          />
        </label>
        <label className="flex min-w-[120px] flex-col gap-1 font-display text-sm uppercase tracking-wide text-muted">
          Giới tính
          <select
            className={inputCls}
            value={gender}
            onChange={(e) => setGender(Number(e.target.value))}
          >
            <option value={1}>Nam (Dương Càn)</option>
            <option value={-1}>Nữ (Âm Khôn)</option>
          </select>
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-vermilion px-5 py-2 font-display text-sm font-semibold uppercase tracking-wide text-cream transition-colors hover:bg-gold-deep disabled:opacity-60"
        >
          {loading ? "Đang tính…" : "Lập lá số"}
        </button>
      </form>

      {error && (
        <p className="mx-auto mt-4 max-w-4xl rounded border border-vermilion/40 bg-vermilion/10 px-4 py-2 text-sm text-vermilion">
          {error}
        </p>
      )}

      {chart && <MenhBanTuTru data={chart} />}
    </main>
  );
}
