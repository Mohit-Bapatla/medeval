"use client";

import Link from "next/link";

import { ApiStatusPanel } from "@/components/api-status";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate, formatMetric, formatNumber } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { DashboardSummary } from "@/types/dashboard";

const navCards = [
  { href: "/documents", title: "Documents", text: "Inspect source text, chunks, and embedding status." },
  { href: "/datasets", title: "Datasets", text: "Review QA examples, answerability, and evidence links." },
  { href: "/experiments", title: "Experiments", text: "Compare runs, metrics, and response traces." },
  { href: "/failures", title: "Failures", text: "Find hallucinations, bad citations, and retrieval misses." },
  { href: "/reports", title: "Reports", text: "Preview computed Markdown and JSON experiment reports." },
];

export default function Home() {
  const { data, error, loading } = useApi<DashboardSummary>("/dashboard/summary");

  return (
    <>
      <PageHeader
        title="MedEval Dashboard"
        description="Open-source healthcare RAG evaluation workflows for traces, metrics, failures, and reproducible reports."
      />
      <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
        <section className="grid gap-4">
          {loading ? <LoadingState label="Loading dashboard summary..." /> : null}
          {error ? <ErrorState message={error} /> : null}
          {data ? (
            <>
              <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
                <p className="text-sm font-semibold text-ink">Development status</p>
                <p className="mt-2 text-sm leading-6 text-graphite">{data.status_note}</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="Documents" value={formatNumber(data.counts.documents)} />
                <MetricCard label="Chunks" value={formatNumber(data.counts.chunks)} />
                <MetricCard label="Datasets" value={formatNumber(data.counts.datasets)} />
                <MetricCard label="QA examples" value={formatNumber(data.counts.qa_examples)} />
                <MetricCard label="Experiments" value={formatNumber(data.counts.experiments)} />
                <MetricCard label="Responses" value={formatNumber(data.counts.model_responses)} />
                <MetricCard label="Evaluations" value={formatNumber(data.counts.evaluation_results)} />
                <MetricCard
                  label="Latest hallucination rate"
                  value={formatMetric(data.latest_experiment?.results.hallucination_rate)}
                />
              </div>
              {data.latest_experiment ? (
                <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase text-graphite">Latest experiment</p>
                      <h2 className="mt-1 text-xl font-semibold">{data.latest_experiment.name}</h2>
                      <p className="mt-2 text-sm text-graphite">
                        Created {formatDate(data.latest_experiment.created_at)}
                      </p>
                    </div>
                    <StatusBadge value={data.latest_experiment.status} />
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <MetricCard
                      label="Examples"
                      value={formatNumber(data.latest_experiment.results.example_count)}
                    />
                    <MetricCard
                      label="Correctness"
                      value={formatMetric(data.latest_experiment.results.avg_correctness)}
                    />
                    <MetricCard
                      label="Groundedness"
                      value={formatMetric(data.latest_experiment.results.avg_groundedness)}
                    />
                  </div>
                  <Link
                    className="mt-4 inline-flex rounded-md bg-clinical px-3 py-2 text-sm font-medium text-white"
                    href={`/experiments/${data.latest_experiment.id}`}
                  >
                    Open experiment
                  </Link>
                </div>
              ) : (
                <EmptyState
                  title="No experiments yet"
                  message="Seed the synthetic documents and QA examples, then run a sample experiment to populate real local metrics."
                />
              )}
            </>
          ) : null}
        </section>
        <aside className="grid gap-4">
          <ApiStatusPanel />
          <div className="grid gap-3">
            {navCards.map((card) => (
              <Link
                className="rounded-lg border border-line bg-white p-4 shadow-sm hover:border-clinical"
                href={card.href}
                key={card.href}
              >
                <p className="font-semibold text-ink">{card.title}</p>
                <p className="mt-2 text-sm leading-6 text-graphite">{card.text}</p>
              </Link>
            ))}
          </div>
        </aside>
      </div>
    </>
  );
}
