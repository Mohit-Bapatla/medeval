export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-danger/30 bg-danger/5 p-5 text-sm">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 shrink-0 text-danger" aria-hidden="true">✕</span>
        <div>
          <p className="font-semibold text-danger">Unable to load data</p>
          <p className="mt-1 text-graphite">{message}</p>
          <p className="mt-2 text-xs text-graphite">
            Ensure the FastAPI backend is running on the configured API URL (default:{" "}
            <code className="rounded bg-surface px-1 py-0.5 font-mono text-ink">
              http://localhost:8000
            </code>
            ).
          </p>
        </div>
      </div>
    </div>
  );
}
