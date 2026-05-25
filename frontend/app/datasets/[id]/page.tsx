"use client";

import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { truncate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { Dataset, QAExample } from "@/types/datasets";

export default function DatasetDetailPage() {
  const params = useParams<{ id: string }>();
  const dataset = useApi<Dataset>(params.id ? `/datasets/${params.id}` : null);
  const examples = useApi<QAExample[]>(
    params.id ? `/datasets/${params.id}/examples` : null,
  );
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [answerabilityFilter, setAnswerabilityFilter] = useState("all");
  const filteredExamples = useMemo(() => {
    return (examples.data ?? []).filter((example) => {
      return (
        (categoryFilter === "all" || example.category === categoryFilter) &&
        (answerabilityFilter === "all" ||
          example.answerability === answerabilityFilter)
      );
    });
  }, [answerabilityFilter, categoryFilter, examples.data]);
  const categories = Array.from(
    new Set((examples.data ?? []).map((example) => example.category)),
  ).sort();
  const answerabilities = Array.from(
    new Set((examples.data ?? []).map((example) => example.answerability)),
  ).sort();

  if (dataset.loading || examples.loading) {
    return <LoadingState label="Loading dataset..." />;
  }
  if (dataset.error) {
    return <ErrorState message={dataset.error} />;
  }
  if (!dataset.data) {
    return (
      <EmptyState
        title="Dataset not found"
        message="The backend did not return this dataset."
        showSeedCommands={false}
      />
    );
  }

  return (
    <>
      <PageHeader
        title={dataset.data.name}
        description="QA examples with answerability labels, difficulty tiers, risk levels, and gold answers for RAG evaluation."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Version" value={dataset.data.version} />
        <MetricCard label="Source" value={dataset.data.source} accent="info" />
        <MetricCard
          label="QA examples"
          value={examples.data?.length ?? "—"}
        />
        <MetricCard
          label="Synthetic"
          value={dataset.data.metadata.synthetic ? "Yes" : "Unknown"}
          accent={dataset.data.metadata.synthetic ? "warning" : undefined}
        />
      </div>

      {dataset.data.metadata.synthetic ? (
        <div className="mt-4">
          <DisclaimerCallout
            message="This dataset contains synthetically generated QA examples. It is not derived from real patient records or clinically validated gold standards."
            compact
          />
        </div>
      ) : null}

      <section className="mt-5 overflow-hidden rounded-lg border border-line bg-white shadow-sm">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 border-b border-line bg-surface/50 px-4 py-3">
          <span className="text-xs font-semibold text-graphite">Filter:</span>
          <select
            className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink focus:border-clinical focus:outline-none"
            onChange={(event) => setCategoryFilter(event.target.value)}
            value={categoryFilter}
          >
            <option value="all">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <select
            className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink focus:border-clinical focus:outline-none"
            onChange={(event) => setAnswerabilityFilter(event.target.value)}
            value={answerabilityFilter}
          >
            <option value="all">All answerability</option>
            {answerabilities.map((answerability) => (
              <option key={answerability} value={answerability}>
                {answerability}
              </option>
            ))}
          </select>
          {(categoryFilter !== "all" || answerabilityFilter !== "all") ? (
            <button
              className="text-xs text-graphite hover:text-ink underline"
              onClick={() => {
                setCategoryFilter("all");
                setAnswerabilityFilter("all");
              }}
              type="button"
            >
              Clear filters
            </button>
          ) : null}
          <span className="ml-auto text-xs text-graphite">
            {filteredExamples.length} of {examples.data?.length ?? 0} examples
          </span>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[800px] border-collapse text-left text-sm">
            <thead className="border-b border-line bg-surface">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Question
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Answerability
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Category
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Difficulty
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Risk
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Gold answer
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {filteredExamples.map((example) => (
                <tr
                  className="align-top transition-colors hover:bg-surface/60"
                  key={example.id}
                >
                  <td className="px-4 py-3.5 font-medium text-ink max-w-xs">
                    {example.question}
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge value={example.answerability} />
                  </td>
                  <td className="px-4 py-3.5 text-sm text-graphite">
                    {example.category}
                  </td>
                  <td className="px-4 py-3.5 text-sm text-graphite">
                    {example.difficulty}
                  </td>
                  <td className="px-4 py-3.5 text-sm text-graphite">
                    {example.risk_level}
                  </td>
                  <td className="px-4 py-3.5 text-sm leading-6 text-graphite max-w-sm">
                    {truncate(example.gold_answer, 140)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {examples.data?.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="No QA examples"
              message="Import JSONL or run the sample QA seed script."
            />
          </div>
        ) : null}
        {examples.data?.length && filteredExamples.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="No matching examples"
              message="Adjust the filters above to see more QA examples."
              showSeedCommands={false}
            />
          </div>
        ) : null}
      </section>
    </>
  );
}
