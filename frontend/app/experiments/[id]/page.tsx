"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { FailureDistributionChart } from "@/components/charts/failure-distribution-chart";
import { MetricBarChart } from "@/components/charts/metric-bar-chart";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate, formatMetric, formatNumber, truncate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { Experiment, ExperimentResponseRow, ExperimentResults } from "@/types/experiments";

export default function ExperimentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const experiment = useApi<Experiment>(id ? `/experiments/${id}` : null);
  const results = useApi<ExperimentResults>(id ? `/experiments/${id}/results` : null);
  const responses = useApi<ExperimentResponseRow[]>(id ? `/experiments/${id}/responses` : null);

  if (experiment.loading || results.loading || responses.loading) {
    return <LoadingState label="Loading experiment..." />;
  }
  if (experiment.error) {
    return <ErrorState message={experiment.error} />;
  }
  if (!experiment.data) {
    return <EmptyState title="Experiment not found" message="The backend did not return this experiment." />;
  }

  const metricData = [
    { name: "Correct", value: results.data?.avg_correctness ?? 0 },
    { name: "Grounded", value: results.data?.avg_groundedness ?? 0 },
    { name: "Cit P", value: results.data?.avg_citation_precision ?? 0 },
    { name: "Cit R", value: results.data?.avg_citation_recall ?? 0 },
    { name: "Ret R", value: results.data?.avg_retrieval_recall ?? 0 },
    { name: "Refusal", value: results.data?.refusal_accuracy ?? 0 },
  ];

  return (
    <>
      <PageHeader
        title={experiment.data.name}
        description="Experiment configuration, aggregate metrics, failure distribution, and response-level traces."
        action={<Link className="rounded-md bg-clinical px-3 py-2 text-sm font-medium text-white" href={`/experiments/${id}/report`}>Open report</Link>}
      />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Status" value={experiment.data.status} />
        <MetricCard label="Examples" value={formatNumber(results.data?.example_count)} />
        <MetricCard label="Correctness" value={formatMetric(results.data?.avg_correctness)} />
        <MetricCard label="Hallucination rate" value={formatMetric(results.data?.hallucination_rate)} />
        <MetricCard label="Groundedness" value={formatMetric(results.data?.avg_groundedness)} />
        <MetricCard label="Citation precision" value={formatMetric(results.data?.avg_citation_precision)} />
        <MetricCard label="Citation recall" value={formatMetric(results.data?.avg_citation_recall)} />
        <MetricCard label="Retrieval recall" value={formatMetric(results.data?.avg_retrieval_recall)} />
      </div>
      <section className="mt-5 grid gap-5 lg:grid-cols-2">
        <MetricBarChart data={metricData} />
        <FailureDistributionChart counts={results.data?.failure_type_counts ?? {}} />
      </section>
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Configuration</h2>
        <div className="mt-3 grid gap-3 text-sm text-graphite md:grid-cols-2">
          <p>Provider/model: {experiment.data.model_provider} / {experiment.data.model_name}</p>
          <p>Embedding: {experiment.data.embedding_model}</p>
          <p>Retrieval: {experiment.data.retrieval_strategy}</p>
          <p>Top-k: {experiment.data.top_k}</p>
          <p>Created: {formatDate(experiment.data.created_at)}</p>
          <p>Temperature: {experiment.data.temperature}</p>
        </div>
      </section>
      <section className="mt-5 overflow-hidden rounded-lg border border-line bg-white shadow-sm">
        <div className="border-b border-line p-4">
          <h2 className="text-lg font-semibold">Model responses</h2>
        </div>
        {responses.error ? <ErrorState message={responses.error} /> : null}
        {responses.data?.length === 0 ? (
          <EmptyState title="No responses" message="Run this experiment to generate response traces." />
        ) : null}
        {responses.data?.length ? (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-surface text-xs uppercase text-graphite">
              <tr>
                <th className="px-4 py-3">Question</th>
                <th className="px-4 py-3">Expected</th>
                <th className="px-4 py-3">Correctness</th>
                <th className="px-4 py-3">Groundedness</th>
                <th className="px-4 py-3">Failure</th>
              </tr>
            </thead>
            <tbody>
              {responses.data.map((response) => (
                <tr className="border-t border-line align-top" key={response.response_id}>
                  <td className="px-4 py-3 font-medium">
                    <Link className="text-clinical hover:underline" href={`/traces/${response.response_id}`}>
                      {truncate(response.question, 120)}
                    </Link>
                  </td>
                  <td className="px-4 py-3"><StatusBadge value={response.expected_answerability} /></td>
                  <td className="px-4 py-3">{formatMetric(response.correctness_score)}</td>
                  <td className="px-4 py-3">{formatMetric(response.groundedness_score)}</td>
                  <td className="px-4 py-3"><StatusBadge value={response.failure_type || "none"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>
    </>
  );
}
