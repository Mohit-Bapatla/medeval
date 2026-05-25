"use client";

import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

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
  const examples = useApi<QAExample[]>(params.id ? `/datasets/${params.id}/examples` : null);
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [answerabilityFilter, setAnswerabilityFilter] = useState("all");
  const filteredExamples = useMemo(() => {
    return (examples.data ?? []).filter((example) => {
      return (
        (categoryFilter === "all" || example.category === categoryFilter) &&
        (answerabilityFilter === "all" || example.answerability === answerabilityFilter)
      );
    });
  }, [answerabilityFilter, categoryFilter, examples.data]);
  const categories = Array.from(new Set((examples.data ?? []).map((example) => example.category))).sort();
  const answerabilities = Array.from(new Set((examples.data ?? []).map((example) => example.answerability))).sort();

  if (dataset.loading || examples.loading) {
    return <LoadingState label="Loading dataset..." />;
  }
  if (dataset.error) {
    return <ErrorState message={dataset.error} />;
  }
  if (!dataset.data) {
    return <EmptyState title="Dataset not found" message="The backend did not return this dataset." />;
  }

  return (
    <>
      <PageHeader title={dataset.data.name} description="QA examples and evaluation labels." />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Version" value={dataset.data.version} />
        <MetricCard label="Source" value={dataset.data.source} />
        <MetricCard label="Examples" value={examples.data?.length ?? 0} />
        <MetricCard label="Synthetic" value={dataset.data.metadata.synthetic ? "yes" : "unknown"} />
      </div>
      <section className="mt-5 overflow-hidden rounded-lg border border-line bg-white shadow-sm">
        <div className="flex flex-wrap gap-2 border-b border-line p-4">
          <select className="rounded-md border border-line bg-white px-3 py-2 text-sm" onChange={(event) => setCategoryFilter(event.target.value)} value={categoryFilter}>
            <option value="all">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          <select className="rounded-md border border-line bg-white px-3 py-2 text-sm" onChange={(event) => setAnswerabilityFilter(event.target.value)} value={answerabilityFilter}>
            <option value="all">All answerability</option>
            {answerabilities.map((answerability) => (
              <option key={answerability} value={answerability}>{answerability}</option>
            ))}
          </select>
        </div>
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-surface text-xs uppercase text-graphite">
            <tr>
              <th className="px-4 py-3">Question</th>
              <th className="px-4 py-3">Answerability</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Difficulty</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Gold answer</th>
            </tr>
          </thead>
          <tbody>
            {filteredExamples.map((example) => (
              <tr className="border-t border-line align-top" key={example.id}>
                <td className="px-4 py-3 font-medium">{example.question}</td>
                <td className="px-4 py-3"><StatusBadge value={example.answerability} /></td>
                <td className="px-4 py-3">{example.category}</td>
                <td className="px-4 py-3">{example.difficulty}</td>
                <td className="px-4 py-3">{example.risk_level}</td>
                <td className="px-4 py-3 text-graphite">{truncate(example.gold_answer, 120)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {examples.data?.length === 0 ? (
          <EmptyState title="No QA examples" message="Import JSONL or run the sample QA seed script." />
        ) : null}
        {examples.data?.length && filteredExamples.length === 0 ? (
          <EmptyState title="No matching examples" message="Adjust the dataset filters to see more QA examples." />
        ) : null}
      </section>
    </>
  );
}
