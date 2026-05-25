export function LoadingState({ label = "Loading data..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-line bg-white px-5 py-4 text-sm text-graphite">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-line border-t-clinical" />
      {label}
    </div>
  );
}
