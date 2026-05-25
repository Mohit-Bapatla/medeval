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
import type { Dataset } from "@/types/datasets";

export default function DatasetsPage() {
  const { data, error, loading } = useApi<Dataset[]>("/datasets");

  return (
    <>
      <PageHeader
        title="Datasets"
        description="QA benchmark datasets with answerability labels, difficulty tiers, risk levels, and evidence-linked gold answers used for RAG evaluation."
      />
      {loading ? <LoadingState label="Loading datasets..." /> : null}
      {error ? <ErrorState message={error} /> : null}
      {data?.length === 0 ? (
        <EmptyState
          title="No datasets found"
          message="Seed synthetic QA examples to review dataset rows and evaluation labels."
        />
      ) : null}
      {data?.length ? (
        <>
          <div className="grid gap-3">
            {data.map((dataset) => (
              <Link
                className="group rounded-lg border border-line bg-white p-5 shadow-sm transition-colors hover:border-clinical"
                href={`/datasets/${dataset.id}`}
                key={dataset.id}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h2 className="font-semibold text-ink group-hover:text-clinical transition-colors">
                        {dataset.name}
                      </h2>
                      <StatusBadge value={dataset.source} />
                    </div>
                    <p className="mt-1.5 text-sm leading-6 text-graphite">
                      {dataset.description || "No description provided."}
                    </p>
                  </div>
                  <span className="text-xs text-graphite shrink-0">
                    v{dataset.version}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-line pt-3">
                  <span className="text-xs text-graphite">
                    Created {formatDate(dataset.created_at)}
                  </span>
                  {dataset.metadata.synthetic ? (
                    <span className="rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                      synthetic data
                    </span>
                  ) : null}
                  <span className="ml-auto text-xs font-medium text-clinical">
                    View examples →
                  </span>
                </div>
              </Link>
            ))}
          </div>
          <div className="mt-5">
            <DisclaimerCallout
              message="These datasets contain synthetically generated QA examples for local evaluation purposes. They are not derived from real patient data and have not been reviewed or validated by clinical experts."
              compact
            />
          </div>
        </>
      ) : null}
    </>
  );
}
