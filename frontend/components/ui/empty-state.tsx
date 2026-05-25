export function EmptyState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white p-6 text-sm text-graphite">
      <p className="font-semibold text-ink">{title}</p>
      <p className="mt-2 leading-6">{message}</p>
      <pre className="mt-4 overflow-x-auto rounded-md bg-surface p-3 text-xs text-graphite">
python scripts/seed_sample_documents.py{"\n"}python scripts/seed_sample_qa.py{"\n"}python scripts/run_sample_experiment.py
      </pre>
    </div>
  );
}
