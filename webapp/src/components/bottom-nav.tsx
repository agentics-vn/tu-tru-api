"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/hom-nay", label: "Hom nay" },
  { href: "/lich", label: "Lich" },
  { href: "/chon-ngay", label: "Chon ngay" },
  { href: "/toi", label: "Toi" },
];

export function BottomNav() {
  const pathname = usePathname();

  // Hide on landing page
  if (pathname === "/") return null;

  return (
    <nav className="bottom-nav">
      <div className="flex items-stretch">
        {TABS.map((tab) => {
          const isActive =
            pathname === tab.href || pathname.startsWith(tab.href + "/");
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`
                flex-1 py-3 text-center transition-colors
                text-[0.65rem] uppercase tracking-[0.15em]
                font-[family-name:var(--font-mono)]
                ${isActive ? "text-fg border-t border-fg" : "text-fg-muted border-t border-transparent"}
              `}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
