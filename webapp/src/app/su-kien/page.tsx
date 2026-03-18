"use client";

import { useState } from "react";
import Link from "next/link";
import { useRequireProfile } from "@/lib/use-require-profile";
import { type SavedEvent } from "@/lib/mock-data";
import { BracketText } from "@/components/bracket-text";
import { formatDate, daysUntil } from "@/lib/utils";

const GRADE_COLORS: Record<string, string> = {
  A: "text-good",
  B: "text-accent",
  C: "text-fg-muted",
  D: "text-bad",
};

const INITIAL_EVENTS: SavedEvent[] = [
  {
    id: "1",
    title: "Khai truong quan cafe",
    date: "2026-04-15",
    intent: "Khai Truong",
    note: "Dia chi: 123 Nguyen Hue, Q1",
    score: 92,
    grade: "A",
    goodHours: ["7h-9h", "11h-13h"],
  },
  {
    id: "2",
    title: "Le dinh hon",
    date: "2026-05-22",
    intent: "Cuoi Hoi",
    score: 87,
    grade: "B",
    goodHours: ["7h-9h", "9h-11h"],
  },
  {
    id: "3",
    title: "Ky hop dong thue mat bang",
    date: "2026-04-10",
    intent: "Ky Hop Dong",
    score: 85,
    grade: "B",
    goodHours: ["11h-13h"],
  },
];

export default function SuKienPage() {
  const { isReady } = useRequireProfile();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [events, setEvents] = useState<SavedEvent[]>(INITIAL_EVENTS);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newIntent, setNewIntent] = useState("");

  if (!isReady) return null;

  const sorted = [...events].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
  const upcoming = sorted.filter((e) => daysUntil(e.date) >= 0);
  const past = sorted.filter((e) => daysUntil(e.date) < 0);

  const handleAddEvent = () => {
    if (!newTitle.trim() || !newDate) return;
    const newEvent: SavedEvent = {
      id: Date.now().toString(),
      title: newTitle.trim(),
      date: newDate,
      intent: newIntent.trim() || "Khac",
    };
    setEvents([...events, newEvent]);
    setNewTitle("");
    setNewDate("");
    setNewIntent("");
    setShowAddForm(false);
  };

  const handleDeleteEvent = (id: string) => {
    setEvents(events.filter((e) => e.id !== id));
    if (expandedId === id) setExpandedId(null);
  };

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
        type="button"
        onClick={() => setShowAddForm(!showAddForm)}
        className="btn-outline w-full mb-6"
      >
        {showAddForm ? "Huy" : "+ Them su kien"}
      </button>

      {/* Add form */}
      {showAddForm && (
        <div className="border border-border p-4 mb-6 space-y-4 page-enter">
          <div>
            <label htmlFor="evt-title" className="mono-label block mb-2">
              Ten su kien
            </label>
            <input
              id="evt-title"
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="VD: Khai truong quan cafe"
              className="w-full bg-transparent border-b border-border py-2 text-sm focus:outline-none focus:border-fg placeholder:text-border"
            />
          </div>
          <div>
            <label htmlFor="evt-date" className="mono-label block mb-2">
              Ngay
            </label>
            <input
              id="evt-date"
              type="date"
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
              className="w-full bg-transparent border-b border-border py-2 text-sm focus:outline-none focus:border-fg"
            />
          </div>
          <div>
            <label htmlFor="evt-intent" className="mono-label block mb-2">
              Loai viec
            </label>
            <input
              id="evt-intent"
              type="text"
              value={newIntent}
              onChange={(e) => setNewIntent(e.target.value)}
              placeholder="VD: Khai Truong"
              className="w-full bg-transparent border-b border-border py-2 text-sm focus:outline-none focus:border-fg placeholder:text-border"
            />
          </div>
          <button
            type="button"
            onClick={handleAddEvent}
            className={`btn-primary w-full ${!newTitle.trim() || !newDate ? "opacity-30 cursor-not-allowed" : ""}`}
            disabled={!newTitle.trim() || !newDate}
          >
            Luu su kien
          </button>
        </div>
      )}

      {/* Upcoming */}
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
              onDelete={() => handleDeleteEvent(evt.id)}
            />
          ))}
        </div>
      )}

      {/* Past */}
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
              onDelete={() => handleDeleteEvent(evt.id)}
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
          <Link href="/chon-ngay" className="btn-primary inline-block">
            Chon ngay tot
          </Link>
        </div>
      )}
    </div>
  );
}

function EventCard({
  event,
  expanded,
  onToggle,
  onDelete,
  isPast,
}: {
  event: SavedEvent;
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  isPast?: boolean;
}) {
  const remaining = daysUntil(event.date);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-expanded={expanded}
      className={`border-t border-border py-4 cursor-pointer ${isPast ? "opacity-50" : ""}`}
      onClick={onToggle}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onToggle();
        }
      }}
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

      <div className="flex gap-2 mt-2">
        <span className="mono-label px-1.5 py-0.5 bg-bg-card">
          {event.intent}
        </span>
        {event.grade && (
          <span
            className={`mono-label px-1.5 py-0.5 ${GRADE_COLORS[event.grade] || "text-fg-muted"}`}
          >
            Hang {event.grade} — {event.score}/100
          </span>
        )}
      </div>

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
            <button
              type="button"
              className="mono-label text-bad ml-auto"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
            >
              Xoa
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
