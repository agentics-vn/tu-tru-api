"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useProfile } from "@/lib/profile-context";
import { mockSavedEvents, type SavedEvent } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";

function daysUntil(dateStr: string): number {
  const target = new Date(dateStr);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function formatDate(d: string) {
  const dt = new Date(d);
  const wd = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
  return `${wd[dt.getDay()]}, ${String(dt.getDate()).padStart(2, "0")}/${String(dt.getMonth() + 1).padStart(2, "0")}/${dt.getFullYear()}`;
}

const GRADE_COLORS = {
  A: "text-good",
  B: "text-accent",
  C: "text-fg-muted",
  D: "text-bad",
};

export default function SuKienPage() {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newIntent, setNewIntent] = useState("");

  const events = useMemo(() => {
    const e = mockSavedEvents();
    return e.sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, []);

  if (isLoaded && !profile) {
    router.replace("/");
    return null;
  }
  if (!isLoaded) return null;

  const upcoming = events.filter((e) => daysUntil(e.date) >= 0);
  const past = events.filter((e) => daysUntil(e.date) < 0);

  return (
    <div className="px-6 py-6 page-enter">
      <header className="flex justify-between items-start mb-8">
        <div className="mono-label">Tu Tru</div>
        <div className="mono-label">Su kien</div>
      </header>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="heading-display text-[2rem] leading-tight">
            Su kien
            <br />
            cua ban
          </h1>
          <p className="text-xs text-fg-muted mt-2 max-w-[220px] leading-relaxed">
            Luu ngay da chon, dem nguoc va nhan nhac gio tot.
          </p>
        </div>
        <BracketText className="mt-1">
          <div className="flex flex-col items-center text-base">
            <span>su</span>
            <span>kien</span>
          </div>
        </BracketText>
      </div>

      {/* Add button */}
      <button
        onClick={() => setShowAddForm(!showAddForm)}
        className="btn-outline w-full mb-6"
      >
        {showAddForm ? "Huy" : "+ Them su kien"}
      </button>

      {/* Add form */}
      {showAddForm && (
        <div className="border border-border p-4 mb-6 space-y-4 page-enter">
          <div>
            <label className="mono-label block mb-2">Ten su kien</label>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="VD: Khai truong quan cafe"
              className="w-full bg-transparent border-b border-border py-2 text-sm focus:outline-none focus:border-fg placeholder:text-border"
            />
          </div>
          <div>
            <label className="mono-label block mb-2">Ngay</label>
            <input
              type="date"
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
              className="w-full bg-transparent border-b border-border py-2 text-sm focus:outline-none focus:border-fg"
            />
          </div>
          <div>
            <label className="mono-label block mb-2">Loai viec</label>
            <input
              type="text"
              value={newIntent}
              onChange={(e) => setNewIntent(e.target.value)}
              placeholder="VD: Khai Truong"
              className="w-full bg-transparent border-b border-border py-2 text-sm focus:outline-none focus:border-fg placeholder:text-border"
            />
          </div>
          <button className="btn-primary w-full">Luu su kien</button>
        </div>
      )}

      {/* Upcoming events */}
      {upcoming.length > 0 && (
        <div className="mb-8">
          <div className="mono-label text-accent mb-4">Sap toi</div>
          {upcoming.map((evt) => (
            <EventCard
              key={evt.id}
              event={evt}
              expanded={expandedId === evt.id}
              onToggle={() =>
                setExpandedId(expandedId === evt.id ? null : evt.id)
              }
            />
          ))}
        </div>
      )}

      {/* Past events */}
      {past.length > 0 && (
        <div className="mb-8">
          <div className="mono-label text-fg-muted mb-4">Da qua</div>
          {past.map((evt) => (
            <EventCard
              key={evt.id}
              event={evt}
              expanded={expandedId === evt.id}
              onToggle={() =>
                setExpandedId(expandedId === evt.id ? null : evt.id)
              }
              isPast
            />
          ))}
        </div>
      )}

      {events.length === 0 && !showAddForm && (
        <div className="text-center py-16">
          <div className="mono-label mb-4">Chua co su kien nao</div>
          <p className="text-xs text-fg-muted mb-6">
            Hay chon ngay tot, sau do luu lai de theo doi.
          </p>
          <button
            onClick={() => router.push("/chon-ngay")}
            className="btn-primary"
          >
            Chon ngay tot
          </button>
        </div>
      )}
    </div>
  );
}

function EventCard({
  event,
  expanded,
  onToggle,
  isPast,
}: {
  event: SavedEvent;
  expanded: boolean;
  onToggle: () => void;
  isPast?: boolean;
}) {
  const remaining = daysUntil(event.date);

  return (
    <div
      className={`border-t border-border py-4 cursor-pointer ${isPast ? "opacity-50" : ""}`}
      onClick={onToggle}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="text-sm font-bold">{event.title}</div>
          <div className="mono-label mt-1">{formatDate(event.date)}</div>
        </div>
        <div className="text-right">
          {!isPast && (
            <div className="heading-display text-2xl text-accent">
              {remaining}
            </div>
          )}
          <div className="mono-label">{isPast ? "Da qua" : "ngay nua"}</div>
        </div>
      </div>

      {/* Tags */}
      <div className="flex gap-2 mt-2">
        <span className="mono-label px-1.5 py-0.5 bg-bg-card">
          {event.intent}
        </span>
        {event.grade && (
          <span
            className={`mono-label px-1.5 py-0.5 ${GRADE_COLORS[event.grade]}`}
          >
            Hang {event.grade} — {event.score}/100
          </span>
        )}
      </div>

      {/* Expanded */}
      {expanded && (
        <div className="mt-4 space-y-3 page-enter">
          {event.note && (
            <p className="text-xs text-fg-muted">{event.note}</p>
          )}
          {event.goodHours && (
            <div>
              <div className="mono-label mb-1">Gio tot</div>
              <div className="flex gap-2">
                {event.goodHours.map((h) => (
                  <span
                    key={h}
                    className="mono-label px-2 py-1 bg-good/10 text-good"
                  >
                    {h}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="flex gap-2 mt-3">
            <button className="mono-label text-accent">Chia se</button>
            <button className="mono-label text-bad ml-auto">Xoa</button>
          </div>
        </div>
      )}
    </div>
  );
}
