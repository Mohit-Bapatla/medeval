"use client";

import Link from "next/link";
import { useState } from "react";

import { apiFetch } from "@/lib/api";
import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { Experiment } from "@/types/experiments";

export default function ExperimentsPage() {
  const experiments = useApi<Experiment[]>("/experiments");
  const [runMessage, setRunMessage] = useState<string | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);

  async function runExperiment(id: string) {
    setRunningId(id);
    setRunMessage("Running deterministic local experiment...");
    try {
      await apiFetch(`/experiments/${id}/run`, { method: "POST" });
      setRunMessage("Experiment completed. Refreshing list...");
      experiments.reload();
    } catch (error) {
      setRunMessage(
        error instanceof Error ? error.message : "Experiment run failed.",
      );
    } finally {
      setRunningId(null);
    }
  }

  return (
    <>
      <PageHeader
        title="Experiments"
        description="Deterministic local evaluation runs over QA datasets — response generation, retrieval, and MVP evaluator scoring. Each run produces traceable per-response results."
      />

      {runMessage ? (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-clinical/30 bg-clinical/5 px-4 py-3 text-sm text-graphite">
          <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-clinical/30 border-t-clinical" />
          {runMessage}
        </div>
      ) : null}

      {experiments.loading ? (
        <LoadingState label="Loading experiments..." />
      ) : null}
      {experiments.error ? <ErrorState message={experiments.error} /> : null}
      {experiments.data?.length === 0 ? (
        <EmptyState
          title="No experiments found"
          message="Seed documents and QA examples, then run a sample experiment to populate evaluation results."
        />
      ) : null}

      {experiments.data?.length ? (
        <>
          <div className="overflow-x-auto rounded-lg border border-line bg-white shadow-sm">
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead className="border-b border-line bg-surface">
                <tr>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Name
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Model
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Retrieval
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Status
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Created
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {experiments.data.map((experiment) => (
                  <tr
                    className="align-middle transition-colors hover:bg-surface/60"
                    key={experiment.id}
                  >
                    <td className="px-4 py-3.5">
                      <Link
                        className="font-semibold text-clinical hover:underline"
                        href={`/experiments/${experiment.id}`}
                      >
                        {experiment.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-graphite">
                      <span className="font-mono text-xs">
                        {experiment.model_name}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-graphite text-sm">
                      {experiment.retrieval_strategy} · top-{experiment.top_k}
                    </td>
                    <td className="px-4 py-3.5">
                      <StatusBadge value={experiment.status} />
                    </td>
                    <td className="px-4 py-3.5 text-sm text-graphite">
                      {formatDate(experiment.created_at)}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex gap-2">
                        <Link
                          className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-graphite transition-colors hover:border-clinical hover:text-clinical"
                          href={`/experiments/${experiment.id}`}
                        >
                          View
                        </Link>
                        <button
                          className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-graphite transition-colors hover:bg-surface disabled:opacity-50"
                          disabled={runningId === experiment.id}
                          onClick={() => void runExperiment(experiment.id)}
                          type="button"
                        >
                          {runningId === experiment.id ? "Running…" : "Re-run"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="border-t border-line px-4 py-2.5">
              <p className="text-xs text-graphite">
                {experiments.data.length} experiment
                {experiments.data.length !== 1 ? "s" : ""} · Deterministic
                local runs
              </p>
            </div>
          </div>

          <div className="mt-5">
            <DisclaimerCallout
              message="These are deterministic local experiments over synthetic data. Results are not validated benchmark scores and should not be interpreted as clinical performance measurements."
              compact
            />
          </div>
        </>
      ) : null}
    </>
  );
}
