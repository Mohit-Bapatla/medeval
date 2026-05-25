export function EmptyState({
  title,
  message,
  showSeedCommands = true,
}: {
  title: string;
  message: string;
  showSeedCommands?: boolean;
}) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white p-8 text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface text-2xl">
        📭
      </div>
      <p className="text-base font-semibold text-ink">{title}</p>
      <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-graphite">
        {message}
      </p>
      {showSeedCommands ? (
        <pre className="mx-auto mt-5 max-w-md overflow-x-auto rounded-md bg-surface px-4 py-3 text-left text-xs leading-5 text-graphite">
          {[
            "python scripts/seed_sample_documents.py",
            "python scripts/seed_sample_qa.py",
            "python scripts/run_sample_experiment.py",
          ].join("\n")}
        </pre>
      ) : null}
    </div>
  );
}
