export function MetricCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string | number;
  helper?: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase text-graphite">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
      {helper ? <p className="mt-2 text-xs leading-5 text-graphite">{helper}</p> : null}
    </div>
  );
}
