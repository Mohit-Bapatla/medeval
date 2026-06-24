export function formatDate(value?: string | null): string {
  if (!value) {
    return "n/a";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatMetric(value?: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

export function formatNumber(value?: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "0";
  }
  return new Intl.NumberFormat("en").format(value);
}

export function truncate(value?: string | null, maxLength = 140): string {
  if (!value) {
    return "";
  }
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxLength - 3)).trimEnd()}...`;
}
