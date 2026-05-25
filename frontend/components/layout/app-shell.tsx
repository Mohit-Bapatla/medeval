"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/documents", label: "Documents" },
  { href: "/datasets", label: "Datasets" },
  { href: "/experiments", label: "Experiments" },
  { href: "/failures", label: "Failures" },
  { href: "/reports", label: "Reports" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-surface text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white lg:block">
        <div className="border-b border-line p-5">
          <p className="text-xs font-semibold uppercase text-clinical">MedEval</p>
          <h1 className="mt-2 text-lg font-semibold text-ink">Reliability Dashboard</h1>
          <p className="mt-2 text-xs leading-5 text-graphite">
            Evaluation traces, metrics, reports, and reproducibility workflows.
          </p>
        </div>
        <nav className="grid gap-1 p-3">
          {navItems.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                className={`rounded-md px-3 py-2 text-sm font-medium ${
                  active
                    ? "bg-clinical text-white"
                    : "text-graphite hover:bg-surface hover:text-ink"
                }`}
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="border-b border-line bg-white px-5 py-4 lg:hidden">
          <p className="text-sm font-semibold text-clinical">MedEval</p>
          <div className="mt-3 flex gap-2 overflow-x-auto">
            {navItems.map((item) => (
              <Link
                className="whitespace-nowrap rounded-md border border-line px-3 py-2 text-sm"
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
      </div>
    </div>
  );
}
