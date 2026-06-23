"use client";

import type { MenhBanPayload } from "@/lib/types";
import { HANH_CLASS } from "@/lib/hanh-colors";

const THAN_SAT_HEADERS = ["Niên Thần", "Nguyệt Thần", "Nhật Thần", "Thời Thần"];
const MENH_HEADERS = ["Mệnh Cung", "Thai Nguyên", "Niên Không", "Nhật Không"];
const KEYS = ["year", "month", "day", "hour"] as const;

function formatDmy(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return iso;
  return `${Number(m[3])}/${Number(m[2])}/${m[1]}`;
}

/** Short zodiac hour label (e.g. Giờ Mão, Giờ Tý Sớm) for the Năm sinh dương row. */
function birthHourDisplay(h: MenhBanPayload["header"]): string {
  if (h.birth_time_label) {
    return h.birth_time_label.split(" (")[0];
  }
  const t = /-\s*([\d]{1,2}:[\d]{2})/.exec(h.duong_lich_display);
  return t?.[1] ?? "";
}

/** Năm sinh dương cells: [năm, tháng, ngày, giờ] */
function birthDateCells(h: MenhBanPayload["header"]): string[] {
  const d = /^(\d{4})-(\d{2})-(\d{2})$/.exec(h.duong_lich);
  const hour = birthHourDisplay(h);
  if (!d) return ["", "", "", hour];
  return [String(Number(d[1])), String(Number(d[2])), String(Number(d[3])), hour];
}

function HanhText({
  text,
  hanh,
  large = false,
}: {
  text: string;
  hanh: string;
  large?: boolean;
}) {
  const cls = HANH_CLASS[hanh as keyof typeof HANH_CLASS] ?? "text-ink";
  return (
    <span
      className={`font-bold ${cls} ${large ? "text-2xl leading-tight md:text-3xl" : ""}`}
    >
      {text}
    </span>
  );
}

/** One full-width row of the sheet: fixed vermilion label column + content area. */
function SheetRow({
  label,
  children,
}: {
  label: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex border-t border-hairline">
      <div className="flex w-24 flex-shrink-0 items-center border-r border-hairline bg-paper-warm px-2 py-2 font-display text-[11px] font-semibold uppercase leading-tight tracking-wide text-vermilion">
        {label}
      </div>
      <div className="flex min-w-0 flex-1 flex-col">{children}</div>
    </div>
  );
}

/** Equal-width columns inside a row's content area. */
function Cols({
  n,
  children,
  className = "",
}: {
  n: number;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`grid grow ${className}`}
      style={{ gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }}
    >
      {children}
    </div>
  );
}

function GCell({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`border-r border-hairline px-2 py-2 text-center align-middle last:border-r-0 ${className}`}
    >
      {children}
    </div>
  );
}

export function MenhBanTuTru({ data }: { data: MenhBanPayload }) {
  const h = data.header;
  const birthCells = birthDateCells(h);

  return (
    <div className="mx-auto max-w-4xl overflow-x-auto p-4">
      <div className="min-w-[760px] overflow-hidden rounded-md border border-gold bg-paper shadow-lg">
        {/* Header band */}
        <div className="flex flex-col gap-4 p-5 md:flex-row md:items-start md:justify-between">
          <div className="md:pr-6">
            <p className="font-display text-xs uppercase tracking-[0.3em] text-gold-deep">
              Luận Giải Bát Tự
            </p>
            <h1 className="mt-1 font-display text-3xl font-bold tracking-wide text-vermilion">
              Mệnh Bàn Tứ Trụ
            </h1>
            <p className="mt-2 text-lg font-semibold text-ink">{h.name || "—"}</p>
          </div>
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-sm text-ink">
            <dt className="font-display uppercase tracking-wide text-muted">Giới tính</dt>
            <dd>{h.gender_label}</dd>
            <dt className="font-display uppercase tracking-wide text-muted">Dương lịch</dt>
            <dd>{h.duong_lich_display}</dd>
            <dt className="font-display uppercase tracking-wide text-muted">Âm lịch</dt>
            <dd>{h.am_lich.display}</dd>
            <dt className="font-display uppercase tracking-wide text-muted">Tiết khí</dt>
            <dd>
              {h.tiet_khi.name} (nguyệt lệnh {h.nguyet_lenh})
            </dd>
            <dt className="font-display uppercase tracking-wide text-muted">Khởi vận</dt>
            <dd className="font-semibold text-vermilion">{formatDmy(h.khoi_van_date)}</dd>
          </dl>
        </div>

        {/* Năm sinh dương */}
        <SheetRow label="Năm sinh dương">
          <Cols n={4}>
            {birthCells.map((v, i) => (
              <GCell key={KEYS[i]} className="text-sm font-semibold text-ink">
                {v || "—"}
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Thập Thần */}
        <SheetRow label="Thập Thần">
          <Cols n={4}>
            {KEYS.map((k) => (
              <GCell key={k} className="text-sm text-ink">
                {k === "day" ? (
                  <span className="font-display font-bold uppercase text-vermilion">
                    {data.pillars[k].thap_than.short_label}
                  </span>
                ) : (
                  data.pillars[k].thap_than.short_label
                )}
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Bát Tự */}
        <SheetRow label="Bát Tự">
          <Cols n={4}>
            {KEYS.map((k) => {
              const p = data.pillars[k];
              return (
                <GCell key={k} className="bg-paper-warm/60 py-3">
                  <div className="flex flex-col items-center gap-1">
                    <HanhText text={p.can.name} hanh={p.can.hanh} large />
                    <HanhText text={p.chi.name} hanh={p.chi.hanh} large />
                  </div>
                </GCell>
              );
            })}
          </Cols>
        </SheetRow>

        {/* Nạp Âm */}
        <SheetRow label="Nạp Âm Ngũ Hành">
          <Cols n={4}>
            {KEYS.map((k) => (
              <GCell key={k} className="text-sm text-ink">
                {data.pillars[k].nap_am.name}
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Can Chi Tàng Ẩn */}
        <SheetRow label="Can Chi Tàng Ẩn">
          <Cols n={4}>
            {KEYS.map((k) => (
              <GCell key={k} className="text-sm">
                <span className="inline-flex flex-wrap justify-center gap-x-2">
                  {data.pillars[k].tang_can.map((t, i) => (
                    <HanhText key={`${t.can_name}-${i}`} text={t.can_name} hanh={t.hanh} />
                  ))}
                </span>
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Phó Tinh */}
        <SheetRow label="Phó Tinh">
          <Cols n={4}>
            {KEYS.map((k) => (
              <GCell key={k} className="text-sm text-ink">
                {data.pillars[k].pho_tinh.map((p) => p.short_label).join("  ")}
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Thập Nhị Thần */}
        <SheetRow label="Thập Nhị Thần">
          <Cols n={4}>
            {KEYS.map((k) => (
              <GCell key={k} className="text-sm text-ink">
                {data.pillars[k].truong_sinh.label_vi}
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Đại Vận */}
        <SheetRow label="Đại Vận">
          <Cols n={data.dai_van.cycles.length}>
            {data.dai_van.cycles.map((c) => (
              <GCell
                key={`dv-${c.start_year}`}
                className="font-display text-sm font-semibold leading-tight text-ink"
              >
                {c.display.split(" ").map((w) => (
                  <div key={w}>{w}</div>
                ))}
              </GCell>
            ))}
          </Cols>
        </SheetRow>
        <SheetRow label="Năm">
          <Cols n={data.dai_van.cycles.length}>
            {data.dai_van.cycles.map((c) => (
              <GCell key={`dvy-${c.start_year}`} className="text-xs">
                <div className="text-vermilion">{c.age_label}</div>
                <div className="text-muted">{c.start_year}</div>
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Lưu Niên */}
        <SheetRow label="Lưu Niên">
          <Cols n={data.luu_nien.length}>
            {data.luu_nien.map((y) => (
              <GCell
                key={`ln-${y.year}`}
                className={`font-display text-sm font-semibold leading-tight text-ink ${
                  y.selected ? "bg-gold/30" : ""
                }`}
              >
                {y.display.split(" ").map((w) => (
                  <div key={w}>{w}</div>
                ))}
              </GCell>
            ))}
          </Cols>
        </SheetRow>
        <SheetRow label="Năm">
          <Cols n={data.luu_nien.length}>
            {data.luu_nien.map((y) => (
              <GCell
                key={`lny-${y.year}`}
                className={`text-xs ${y.selected ? "bg-gold/30" : ""}`}
              >
                <div className="text-vermilion">{y.year}</div>
                <div className="text-muted">{y.age_label}</div>
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Thần Sát Nguyên Cục */}
        <SheetRow label="Thần Sát Nguyên Cục">
          <Cols n={4}>
            {THAN_SAT_HEADERS.map((label) => (
              <GCell
                key={label}
                className="bg-paper-warm font-display text-xs font-semibold uppercase tracking-wide text-jade"
              >
                {label}
              </GCell>
            ))}
          </Cols>
          <Cols n={4} className="border-t border-hairline">
            {KEYS.map((k) => (
              <GCell key={k} className="align-top text-sm text-ink">
                {data.pillars[k].than_sat.length > 0 ? (
                  <div className="flex flex-col gap-0.5">
                    {data.pillars[k].than_sat.map((s) => (
                      <span key={s.key}>{s.name}</span>
                    ))}
                  </div>
                ) : (
                  <span className="text-muted">—</span>
                )}
              </GCell>
            ))}
          </Cols>
        </SheetRow>

        {/* Mệnh */}
        <SheetRow label="Mệnh">
          <Cols n={4}>
            {MENH_HEADERS.map((label) => (
              <GCell
                key={label}
                className="bg-paper-warm font-display text-xs font-semibold uppercase tracking-wide text-jade"
              >
                {label}
              </GCell>
            ))}
          </Cols>
          <Cols n={4} className="border-t border-hairline">
            <GCell className="text-sm font-semibold text-ink">
              {data.menh_cung.display}
            </GCell>
            <GCell className="text-sm font-semibold text-ink">
              {data.thai_nguyen.display}
            </GCell>
            <GCell className="text-sm text-ink">
              {data.tuan_khong.nien_khong.display}
            </GCell>
            <GCell className="text-sm text-ink">
              {data.tuan_khong.nhat_khong.display}
            </GCell>
          </Cols>
        </SheetRow>
      </div>
    </div>
  );
}
