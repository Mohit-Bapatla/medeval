"use client";

import Link from "next/link";

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
        description="QA benchmark datasets, answerability labels, and evidence-linked examples."
      />
      {loading ? <LoadingState label="Loading datasets..." /> : null}
      {error ? <ErrorState message={error} /> : null}
      {data?.length === 0 ? (
        <EmptyState title="No datasets found" message="Seed synthetic QA examples to review dataset rows." />
      ) : null}
      <div className="grid gap-3">
        {data?.map((dataset) => (
          <Link
            className="rounded-lg border border-line bg-white p-4 shadow-sm hover:border-clinical"
            href={`/datasets/${dataset.id}`}
            key={dataset.id}
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="font-semibold">{dataset.name}</h2>
                <p className="mt-2 text-sm text-graphite">{dataset.description || "No description"}</p>
              </div>
              <StatusBadge value={dataset.source} />
            </div>
            <p className="mt-3 text-xs text-graphite">
              Version {dataset.version} - Created {formatDate(dataset.created_at)}
            </p>
          </Link>
        ))}
      </div>
    </>
  );
}
