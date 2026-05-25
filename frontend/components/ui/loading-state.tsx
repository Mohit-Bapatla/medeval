export function LoadingState({ label = "Loading data..." }: { label?: string }) {
  return (
    <div className="rounded-lg border border-line bg-white p-6 text-sm text-graphite">
      {label}
    </div>
  );
}
