export function StatusBadge({ value }: { value?: string | boolean | null }) {
  const label = typeof value === "boolean" ? (value ? "true" : "false") : value || "unknown";
  const normalized = label.toLowerCase();
  const className = normalized.includes("fail") || normalized === "true"
    ? "border-signal/30 bg-signal/10 text-signal"
    : normalized.includes("complete") || normalized.includes("answerable") || normalized === "none"
      ? "border-clinical/30 bg-clinical/10 text-clinical"
      : "border-line bg-surface text-graphite";

  return (
    <span className={`inline-flex w-fit rounded-full border px-2.5 py-1 text-xs font-medium ${className}`}>
      {label}
    </span>
  );
}
