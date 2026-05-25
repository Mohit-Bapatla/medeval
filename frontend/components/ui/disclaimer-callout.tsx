export function DisclaimerCallout({
  message,
  compact = false,
}: {
  message: string;
  compact?: boolean;
}) {
  return (
    <div
      className={`flex gap-3 rounded-lg border border-signal/30 bg-signal/5 ${
        compact ? "p-3" : "p-4"
      }`}
    >
      <span
        aria-hidden="true"
        className="mt-0.5 shrink-0 text-signal"
      >
        ⚠
      </span>
      <p className={`leading-6 text-graphite ${compact ? "text-xs" : "text-sm"}`}>
        <span className="font-semibold text-ink">Disclaimer: </span>
        {message}
      </p>
    </div>
  );
}
