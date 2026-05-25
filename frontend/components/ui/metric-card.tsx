export function MetricCard({
  label,
  value,
  helper,
  accent,
}: {
  label: string;
  value: string | number;
  helper?: string;
  accent?: "danger" | "success" | "warning" | "info";
}) {
  const accentBorder =
    accent === "danger"
      ? "border-l-4 border-l-danger"
      : accent === "success"
        ? "border-l-4 border-l-success"
        : accent === "warning"
          ? "border-l-4 border-l-signal"
          : accent === "info"
            ? "border-l-4 border-l-clinical"
            : "";

  return (
    <div
      className={`rounded-lg border border-line bg-white p-4 shadow-sm ${accentBorder}`}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-graphite">
        {label}
      </p>
      <p className="mt-1.5 text-2xl font-bold tabular-nums text-ink">{value}</p>
      {helper ? (
        <p className="mt-1.5 text-xs leading-5 text-graphite">{helper}</p>
      ) : null}
    </div>
  );
}
