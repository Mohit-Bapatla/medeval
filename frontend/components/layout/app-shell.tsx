"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview", icon: "◎" },
  { href: "/documents", label: "Documents", icon: "📄" },
  { href: "/datasets", label: "Datasets", icon: "🗂" },
  { href: "/experiments", label: "Experiments", icon: "⚗" },
  { href: "/failures", label: "Failures", icon: "⚠" },
  { href: "/human-review", label: "Human Review", icon: "✓" },
  { href: "/reports", label: "Reports", icon: "📊" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-surface text-ink">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-line bg-white lg:flex">
        {/* Brand */}
        <div className="border-b border-line px-5 py-5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-clinical text-sm font-bold text-white shadow-sm">
              M
            </div>
            <div>
              <p className="text-sm font-bold tracking-tight text-ink">MedEval</p>
              <p className="text-xs text-graphite">v0.1 · open-source</p>
            </div>
          </div>
          <p className="mt-3 text-xs leading-5 text-graphite">
            Healthcare RAG evaluation &amp; reliability platform. Measures
            hallucinations, citation grounding, and retrieval quality.
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-3">
          <p className="mb-1 px-3 text-xs font-semibold uppercase tracking-wider text-graphite/60">
            Platform
          </p>
          <div className="grid gap-0.5">
            {navItems.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? "bg-clinical text-white"
                      : "text-graphite hover:bg-surface hover:text-ink"
                  }`}
                  href={item.href}
                  key={item.href}
                >
                  <span className={`w-4 text-center text-xs ${active ? "text-white/80" : "text-graphite/60"}`} aria-hidden="true">
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Footer */}
        <div className="border-t border-line px-5 py-4">
          <p className="text-xs leading-5 text-graphite">
            Synthetic demo data only. No clinical validation. No external
            AI calls.
          </p>
          <a
            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-clinical hover:underline"
            href="https://github.com/Mohit-Bapatla/medeval"
            rel="noopener noreferrer"
            target="_blank"
          >
            GitHub ↗
          </a>
        </div>
      </aside>

      {/* Content area */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <header className="sticky top-0 z-10 border-b border-line bg-white/95 px-5 py-3 backdrop-blur-sm lg:hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-clinical text-xs font-bold text-white">
                M
              </div>
              <span className="text-sm font-bold text-ink">MedEval</span>
            </div>
          </div>
          <nav className="mt-3 flex gap-1.5 overflow-x-auto pb-1">
            {navItems.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  className={`whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                    active
                      ? "bg-clinical text-white"
                      : "border border-line text-graphite hover:bg-surface"
                  }`}
                  href={item.href}
                  key={item.href}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </header>

        <main className="mx-auto max-w-7xl px-5 py-7">{children}</main>
      </div>
    </div>
  );
}
