"use client";

import Link from "next/link";

import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
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
        description="Computed evaluation summaries per experiment — exportable as Markdown, JSON, and CSV. Reports are generated on demand from local evaluation results."
      />
      {experiments.loading ? (
        <LoadingState label="Loading report candidates..." />
      ) : null}
      {experiments.error ? <ErrorState message={experiments.error} /> : null}
      {experiments.data?.length === 0 ? (
        <EmptyState
          title="No reports available"
          message="Run an experiment to generate a computed report preview."
        />
      ) : null}
      {experiments.data?.length ? (
        <>
          <div className="grid gap-3">
            {experiments.data.map((experiment) => (
              <Link
                className="group rounded-lg border border-line bg-white p-5 shadow-sm transition-colors hover:border-clinical"
                href={`/experiments/${experiment.id}/report`}
                key={experiment.id}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-base" aria-hidden="true">
                        📊
                      </span>
                      <h2 className="font-semibold text-ink group-hover:text-clinical transition-colors">
                        {experiment.name}
                      </h2>
                    </div>
                    <p className="mt-1.5 text-sm text-graphite">
                      <span className="font-mono text-xs">
                        {experiment.model_provider} / {experiment.model_name}
                      </span>
                      {" · "}
                      created {formatDate(experiment.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <StatusBadge value={experiment.status} />
                    <span className="text-xs font-medium text-clinical">
                      View report →
                    </span>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 border-t border-line pt-3">
                  <span className="rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs text-graphite">
                    Markdown
                  </span>
                  <span className="rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs text-graphite">
                    JSON
                  </span>
                  <span className="rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs text-graphite">
                    CSV
                  </span>
                </div>
              </Link>
            ))}
          </div>
          <div className="mt-5">
            <DisclaimerCallout
              message="Reports are generated from local deterministic runs over seeded data, including the MedEval v1 public healthcare seed. They are not clinical validation, medical advice, or a real model leaderboard."
              compact
            />
          </div>
        </>
      ) : null}
    </>
  );
}
