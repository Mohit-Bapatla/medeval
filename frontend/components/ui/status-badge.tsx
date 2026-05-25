function getBadgeStyle(normalized: string): string {
  // Danger — red: hallucination, failure, incorrect, unsupported, error, miss, refused
  if (
    normalized.includes("hallucinat") ||
    normalized === "failed_refusal" ||
    normalized.includes("incorrect") ||
    normalized === "unsupported" ||
    normalized.includes("error") ||
    normalized.includes("miss") ||
    normalized === "not embedded" ||
    (normalized.includes("fail") && !normalized.includes("refusal"))
  ) {
    return "border-danger/30 bg-danger/10 text-danger";
  }

  // Warning — amber: partial, ambiguous, unsure, over_refusal, unknown, signal
  if (
    normalized.includes("partial") ||
    normalized.includes("ambiguous") ||
    normalized.includes("unsure") ||
    normalized === "over_refusal" ||
    normalized === "unknown" ||
    normalized === "offline" ||
    normalized === "checking"
  ) {
    return "border-signal/30 bg-signal/10 text-signal";
  }

  // Success — green: complete, answerable, correct, grounded, cited, embedded, none, connected, success
  if (
    normalized.includes("complete") ||
    normalized === "answerable" ||
    normalized === "none" ||
    normalized.includes("correct") ||
    normalized.includes("grounded") ||
    normalized === "cited" ||
    normalized.includes("embedded") ||
    normalized.includes("connect") ||
    normalized.includes("success") ||
    normalized === "correct_refusal" ||
    normalized === "supported"
  ) {
    return "border-success/30 bg-success/10 text-success";
  }

  // Info — blue/slate: retrieved, not_applicable, synthetic, local
  if (
    normalized === "retrieved" ||
    normalized === "not_applicable" ||
    normalized.includes("synthetic") ||
    normalized.includes("guideline") ||
    normalized.includes("protocol") ||
    normalized.includes("policy")
  ) {
    return "border-blue-200 bg-blue-50 text-blue-700";
  }

  // Default neutral
  return "border-line bg-surface text-graphite";
}

export function StatusBadge({ value }: { value?: string | boolean | null }) {
  const label =
    typeof value === "boolean" ? (value ? "true" : "false") : (value ?? "unknown");
  const normalized = label.toLowerCase();
  const className = getBadgeStyle(normalized);

  return (
    <span
      className={`inline-flex w-fit items-center rounded-full border px-2.5 py-0.5 text-xs font-medium leading-5 ${className}`}
    >
      {label}
    </span>
  );
}
