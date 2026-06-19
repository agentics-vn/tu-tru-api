"use client";

import type { MenhBanPayload } from "@/lib/types";
import { HANH_CLASS } from "@/lib/hanh-colors";

const PILLAR_LABELS: Record<string, string> = {
  year: "Năm",
  month: "Tháng",
  day: "Ngày",
  hour: "Giờ",
};

const THAN_SAT_HEADERS = ["Niên Thần", "Nguyệt Thần", "Nhật Thần", "Thời Thần"];
const KEYS = ["year", "month", "day", "hour"] as const;

function formatDmy(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return iso;
  return `${Number(m[3])}/${Number(m[2])}/${m[1]}`;
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

/** Left-hand row label column (vermilion, condensed, uppercase) — matches the source grid. */
function RowLabel({ children }: { children: React.ReactNode }) {
  return (
    <th className="w-24 border border-hairline bg-paper-warm px-2 py-2 text-left align-middle font-display text-[11px] font-semibold uppercase leading-tight tracking-wide text-vermilion">
      {children}
    </th>
  );
}

function Cell({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <td
      className={`border border-hairline px-2 py-2 text-center align-middle ${className}`}
    >
      {children}
    </td>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 font-display text-sm font-semibold uppercase tracking-[0.15em] text-jade">
      {children}
    </p>
  );
}

export function MenhBanTuTru({ data }: { data: MenhBanPayload }) {
  const h = data.header;

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-4">
      {/* Header band */}
      <div className="overflow-hidden rounded-lg border border-gold/50 bg-paper shadow-lg">
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <div className="border-b border-hairline pb-3 md:border-b-0 md:border-r md:pb-0 md:pr-4">
            <p className="font-display text-xs uppercase tracking-[0.3em] text-gold-deep">
              Luận Giải Bát Tự
            </p>
            <h1 className="mt-1 font-display text-3xl font-bold tracking-wide text-vermilion">
              Mệnh Bàn Tứ Trụ
            </h1>
            <p className="mt-2 text-lg font-semibold text-ink">
              {h.name || "—"}
            </p>
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
      </div>

      {/* Main Tứ Trụ grid */}
      <div className="overflow-x-auto rounded-lg border border-gold/50 bg-paper shadow-lg">
        <table className="w-full min-w-[640px] border-collapse">
          <thead>
            <tr>
              <RowLabel> </RowLabel>
              {KEYS.map((k) => (
                <Cell key={k} className="bg-paper-warm font-display text-sm font-semibold uppercase tracking-wide text-jade">
                  {PILLAR_LABELS[k]}
                </Cell>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <RowLabel>Thập Thần</RowLabel>
              {KEYS.map((k) => (
                <Cell key={k} className="text-sm text-ink">
                  {k === "day" ? (
                    <span className="font-display font-bold uppercase text-vermilion">
                      {data.pillars[k].thap_than.short_label}
                    </span>
                  ) : (
                    data.pillars[k].thap_than.short_label
                  )}
                </Cell>
              ))}
            </tr>
            <tr>
              <RowLabel>Bát Tự</RowLabel>
              {KEYS.map((k) => {
                const p = data.pillars[k];
                return (
                  <Cell key={k} className="bg-paper-warm/60">
                    <div className="flex flex-col items-center gap-1">
                      <HanhText text={p.can.name} hanh={p.can.hanh} large />
                      <HanhText text={p.chi.name} hanh={p.chi.hanh} large />
                    </div>
                  </Cell>
                );
              })}
            </tr>
            <tr>
              <RowLabel>Nạp Âm Ngũ Hành</RowLabel>
              {KEYS.map((k) => (
                <Cell key={k} className="text-sm text-ink">
                  {data.pillars[k].nap_am.name}
                </Cell>
              ))}
            </tr>
            <tr>
              <RowLabel>Can Chi Tàng Ẩn</RowLabel>
              {KEYS.map((k) => (
                <Cell key={k} className="text-sm">
                  <span className="inline-flex flex-wrap justify-center gap-x-2">
                    {data.pillars[k].tang_can.map((t, i) => (
                      <HanhText key={`${t.can_name}-${i}`} text={t.can_name} hanh={t.hanh} />
                    ))}
                  </span>
                </Cell>
              ))}
            </tr>
            <tr>
              <RowLabel>Phó Tinh</RowLabel>
              {KEYS.map((k) => (
                <Cell key={k} className="text-sm text-ink">
                  {data.pillars[k].pho_tinh.map((p) => p.short_label).join("  ")}
                </Cell>
              ))}
            </tr>
            <tr>
              <RowLabel>Thập Nhị Thần</RowLabel>
              {KEYS.map((k) => (
                <Cell key={k} className="text-sm text-ink">
                  {data.pillars[k].truong_sinh.label_vi}
                </Cell>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Đại Vận */}
      <div className="overflow-x-auto rounded-lg border border-gold/50 bg-paper p-4 shadow-lg">
        <SectionTitle>Đại Vận</SectionTitle>
        <table className="w-full min-w-[680px] border-collapse text-center">
          <tbody>
            <tr>
              {data.dai_van.cycles.map((c) => (
                <td
                  key={`dv-${c.start_year}`}
                  className="border border-hairline px-2 py-1.5 align-top"
                >
                  <div className="font-display font-semibold leading-tight text-ink">
                    {c.display.split(" ").map((w) => (
                      <div key={w}>{w}</div>
                    ))}
                  </div>
                </td>
              ))}
            </tr>
            <tr>
              {data.dai_van.cycles.map((c) => (
                <td
                  key={`dvy-${c.start_year}`}
                  className="border border-hairline px-2 py-1 text-xs"
                >
                  <div className="text-vermilion">{c.age_label}</div>
                  <div className="text-muted">{c.start_year}</div>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Lưu Niên */}
      <div className="overflow-x-auto rounded-lg border border-gold/50 bg-paper p-4 shadow-lg">
        <SectionTitle>Lưu Niên</SectionTitle>
        <table className="w-full min-w-[680px] border-collapse text-center">
          <tbody>
            <tr>
              {data.luu_nien.map((y) => (
                <td
                  key={`ln-${y.year}`}
                  className={`border border-hairline px-2 py-1.5 font-display font-semibold leading-tight text-ink ${
                    y.selected ? "bg-gold/30" : ""
                  }`}
                >
                  {y.display.split(" ").map((w) => (
                    <div key={w}>{w}</div>
                  ))}
                </td>
              ))}
            </tr>
            <tr>
              {data.luu_nien.map((y) => (
                <td
                  key={`lny-${y.year}`}
                  className={`border border-hairline px-2 py-1 text-xs ${
                    y.selected ? "bg-gold/30" : ""
                  }`}
                >
                  <div className="text-vermilion">{y.year}</div>
                  <div className="text-muted">{y.age_label}</div>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Thần Sát */}
      <div className="overflow-x-auto rounded-lg border border-gold/50 bg-paper p-4 shadow-lg">
        <SectionTitle>Thần Sát Nguyên Cục</SectionTitle>
        <table className="w-full border-collapse text-center">
          <thead>
            <tr>
              {THAN_SAT_HEADERS.map((label) => (
                <Cell
                  key={label}
                  className="bg-paper-warm font-display text-xs font-semibold uppercase tracking-wide text-jade"
                >
                  {label}
                </Cell>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {KEYS.map((k) => (
                <Cell key={k} className="align-top text-sm text-ink">
                  {data.pillars[k].than_sat.length > 0 ? (
                    <div className="flex flex-col gap-0.5">
                      {data.pillars[k].than_sat.map((s) => (
                        <span key={s.key}>{s.name}</span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </Cell>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Mệnh */}
      <div className="overflow-x-auto rounded-lg border border-gold/50 bg-paper p-4 shadow-lg">
        <SectionTitle>Mệnh</SectionTitle>
        <table className="w-full border-collapse text-center">
          <thead>
            <tr>
              {["Mệnh Cung", "Thai Nguyên", "Niên Không", "Nhật Không"].map((label) => (
                <Cell
                  key={label}
                  className="bg-paper-warm font-display text-xs font-semibold uppercase tracking-wide text-jade"
                >
                  {label}
                </Cell>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <Cell className="text-sm font-semibold text-ink">
                {data.menh_cung.display}
              </Cell>
              <Cell className="text-sm font-semibold text-ink">
                {data.thai_nguyen.display}
              </Cell>
              <Cell className="text-sm text-ink">
                {data.tuan_khong.nien_khong.display}
              </Cell>
              <Cell className="text-sm text-ink">
                {data.tuan_khong.nhat_khong.display}
              </Cell>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
