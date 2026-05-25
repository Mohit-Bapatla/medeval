"use client";

import Link from "next/link";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { Experiment } from "@/types/experiments";

export default function ReportsPage() {
  const experiments = useApi<Experiment[]>("/experiments");

  return (
    <>
      <PageHeader
        title="Reports"
        description="Computed Markdown and JSON summaries for local experiments. No PDF export or persisted report artifacts in Batch 3."
      />
      {experiments.loading ? <LoadingState label="Loading report candidates..." /> : null}
      {experiments.error ? <ErrorState message={experiments.error} /> : null}
      {experiments.data?.length === 0 ? (
        <EmptyState title="No reports available" message="Run an experiment to preview a computed report." />
      ) : null}
      <div className="grid gap-3">
        {experiments.data?.map((experiment) => (
          <Link
            className="rounded-lg border border-line bg-white p-4 shadow-sm hover:border-clinical"
            href={`/experiments/${experiment.id}/report`}
            key={experiment.id}
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="font-semibold">{experiment.name}</h2>
                <p className="mt-2 text-sm text-graphite">
                  {experiment.model_provider} / {experiment.model_name} - created {formatDate(experiment.created_at)}
                </p>
              </div>
              <StatusBadge value={experiment.status} />
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
