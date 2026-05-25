"use client";

import Link from "next/link";
import { useState } from "react";

import { apiFetch } from "@/lib/api";
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

  async function runExperiment(id: string) {
    setRunMessage("Running deterministic local experiment...");
    try {
      await apiFetch(`/experiments/${id}/run`, { method: "POST" });
      setRunMessage("Experiment run completed. Refreshing list...");
      experiments.reload();
    } catch (error) {
      setRunMessage(error instanceof Error ? error.message : "Experiment run failed");
    }
  }

  return (
    <>
      <PageHeader
        title="Experiments"
        description="Synchronous deterministic local runs over QA datasets, with response traces and MVP evaluator metrics."
      />
      {runMessage ? (
        <div className="mb-4 rounded-lg border border-line bg-white p-3 text-sm text-graphite">
          {runMessage}
        </div>
      ) : null}
      {experiments.loading ? <LoadingState label="Loading experiments..." /> : null}
      {experiments.error ? <ErrorState message={experiments.error} /> : null}
      {experiments.data?.length === 0 ? (
        <EmptyState
          title="No experiments found"
          message="Seed documents and QA examples, then run a sample experiment to populate results."
        />
      ) : null}
      <div className="overflow-hidden rounded-lg border border-line bg-white shadow-sm">
        {experiments.data?.length ? (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-surface text-xs uppercase text-graphite">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Retrieval</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {experiments.data.map((experiment) => (
                <tr className="border-t border-line" key={experiment.id}>
                  <td className="px-4 py-3 font-medium">
                    <Link className="text-clinical hover:underline" href={`/experiments/${experiment.id}`}>
                      {experiment.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{experiment.model_name}</td>
                  <td className="px-4 py-3">{experiment.retrieval_strategy} - top {experiment.top_k}</td>
                  <td className="px-4 py-3"><StatusBadge value={experiment.status} /></td>
                  <td className="px-4 py-3">{formatDate(experiment.created_at)}</td>
                  <td className="px-4 py-3">
                    <button
                      className="rounded-md border border-line px-3 py-1.5 text-xs font-medium hover:bg-surface"
                      onClick={() => void runExperiment(experiment.id)}
                      type="button"
                    >
                      Run
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </>
  );
}
