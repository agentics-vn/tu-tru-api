"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useCallback } from "react";

const TABS = [
  { href: "/hom-nay", label: "Hom nay" },
  { href: "/lich", label: "Lich" },
  { href: "/chon-ngay", label: "Chon ngay" },
  { href: "/toi", label: "Toi" },
];

const MORE_LINKS = [
  { href: "/hop-tuoi", label: "Hop tuoi doi lua" },
  { href: "/phong-thuy", label: "Phong thuy ca nhan" },
  { href: "/so-sanh", label: "So sanh 2 ngay" },
  { href: "/su-kien", label: "Su kien cua ban" },
  { href: "/chia-se", label: "Chia se ngay hom nay" },
];

export function BottomNav() {
  const pathname = usePathname();
  const [showMore, setShowMore] = useState(false);

  // Close menu on Escape key
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape" && showMore) setShowMore(false);
  }, [showMore]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Hide on landing page
  if (pathname === "/") return null;

  const isMoreActive = MORE_LINKS.some(
    (l) => pathname === l.href || pathname.startsWith(l.href + "/")
  );

  return (
    <>
      {/* More menu overlay */}
      {showMore && (
        <div
          className="fixed inset-0 z-40 bg-fg/10"
          onClick={() => setShowMore(false)}
        >
          <div
            className="absolute bottom-12 left-1/2 -translate-x-1/2 w-full max-w-[430px] bg-bg border-t border-border"
            role="menu"
            onClick={(e) => e.stopPropagation()}
          >
            {MORE_LINKS.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  role="menuitem"
                  onClick={() => setShowMore(false)}
                  className={`
                    block py-3 px-6 text-[0.65rem] uppercase tracking-[0.15em]
                    font-[family-name:var(--font-mono)]
                    border-b border-border transition-colors
                    ${active ? "text-fg bg-bg-card" : "text-fg-muted"}
                  `}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}

      <nav className="bottom-nav" aria-label="Dieu huong chinh">
        <div className="flex items-stretch">
          {TABS.map((tab) => {
            const isActive =
              pathname === tab.href || pathname.startsWith(tab.href + "/");
            return (
              <Link
                key={tab.href}
                href={tab.href}
                aria-current={isActive ? "page" : undefined}
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
          <button
            type="button"
            onClick={() => setShowMore(!showMore)}
            aria-expanded={showMore}
            aria-haspopup="menu"
            className={`
              flex-1 py-3 text-center transition-colors
              text-[0.65rem] uppercase tracking-[0.15em]
              font-[family-name:var(--font-mono)]
              ${isMoreActive || showMore ? "text-fg border-t border-fg" : "text-fg-muted border-t border-transparent"}
            `}
          >
            Them
          </button>
        </div>
      </nav>
    </>
  );
}
