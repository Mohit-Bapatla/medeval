"use client";

import Link from "next/link";

import { ApiStatusPanel } from "@/components/api-status";
import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
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
  {
    href: "/documents",
    title: "Documents",
    icon: "📄",
    text: "Inspect source text, cleaned chunks, and embedding status.",
  },
  {
    href: "/datasets",
    title: "Datasets",
    icon: "🗂",
    text: "Review QA benchmarks, answerability labels, and evidence links.",
  },
  {
    href: "/experiments",
    title: "Experiments",
    icon: "⚗",
    text: "Compare evaluation runs, aggregate metrics, and response traces.",
  },
  {
    href: "/failures",
    title: "Failure Analysis",
    icon: "⚠",
    text: "Find hallucinations, citation failures, and retrieval misses.",
  },
  {
    href: "/reports",
    title: "Reports",
    icon: "📊",
    text: "Preview and export Markdown/JSON/CSV experiment reports.",
  },
];

export default function Home() {
  const { data, error, loading } = useApi<DashboardSummary>("/dashboard/summary");

  return (
    <>
      {/* Hero header */}
      <div className="mb-7 border-b border-line pb-7">
        <div className="flex items-center gap-2 mb-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-clinical text-white text-base font-bold shadow-sm">
            M
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-ink">MedEval</h1>
        </div>
        <p className="text-base font-semibold text-graphite mt-1">
          Healthcare RAG Evaluation &amp; Reliability Platform
        </p>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-graphite">
          Measure hallucinations, citation grounding, refusal behavior, retrieval quality, latency,
          and cost across reproducible RAG experiments on synthetic healthcare QA datasets.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {[
            "Hallucination detection",
            "Citation grounding",
            "Refusal accuracy",
            "Retrieval recall",
            "Claim-level support",
            "Reproducible experiments",
          ].map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-clinical/30 bg-clinical/5 px-3 py-1 text-xs font-medium text-clinical"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <section className="grid gap-5">
          {loading ? <LoadingState label="Loading dashboard summary..." /> : null}
          {error ? <ErrorState message={error} /> : null}
          {data ? (
            <>
              {/* Status note */}
              <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wide text-graphite">
                  Development status
                </p>
                <p className="mt-1.5 text-sm leading-6 text-graphite">
                  {data.status_note}
                </p>
              </div>

              {/* Metric cards */}
              <div>
                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Platform metrics
                </p>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
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
                    accent={
                      data.latest_experiment?.results.hallucination_rate != null
                        ? data.latest_experiment.results.hallucination_rate > 0.3
                          ? "danger"
                          : data.latest_experiment.results.hallucination_rate > 0.1
                            ? "warning"
                            : "success"
                        : undefined
                    }
                  />
                </div>
              </div>

              {/* Latest experiment */}
              {data.latest_experiment ? (
                <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-graphite">
                        Latest experiment
                      </p>
                      <h2 className="mt-1.5 text-xl font-bold text-ink">
                        {data.latest_experiment.name}
                      </h2>
                      <p className="mt-1 text-sm text-graphite">
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
                      label="Avg Correctness"
                      value={formatMetric(data.latest_experiment.results.avg_correctness)}
                      accent={
                        data.latest_experiment.results.avg_correctness != null
                          ? data.latest_experiment.results.avg_correctness >= 0.75
                            ? "success"
                            : data.latest_experiment.results.avg_correctness >= 0.5
                              ? "warning"
                              : "danger"
                          : undefined
                      }
                    />
                    <MetricCard
                      label="Avg Groundedness"
                      value={formatMetric(data.latest_experiment.results.avg_groundedness)}
                      accent={
                        data.latest_experiment.results.avg_groundedness != null
                          ? data.latest_experiment.results.avg_groundedness >= 0.75
                            ? "success"
                            : data.latest_experiment.results.avg_groundedness >= 0.5
                              ? "warning"
                              : "danger"
                          : undefined
                      }
                    />
                  </div>
                  <Link
                    className="mt-4 inline-flex items-center gap-1.5 rounded-md bg-clinical px-4 py-2 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-90"
                    href={`/experiments/${data.latest_experiment.id}`}
                  >
                    View experiment →
                  </Link>
                </div>
              ) : (
                <EmptyState
                  title="No experiments yet"
                  message="Seed the synthetic documents and QA examples, then run a sample experiment to populate local evaluation metrics."
                />
              )}

              <DisclaimerCallout message="All metrics shown are computed from locally seeded synthetic data. Results are deterministic and reproducible but are not validated benchmark scores, clinical ground truth, or production system measurements." />
            </>
          ) : null}
        </section>

        <aside className="grid gap-4 content-start">
          <ApiStatusPanel />
          <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-graphite">
              Navigate
            </p>
            <div className="grid gap-2">
              {navCards.map((card) => (
                <Link
                  className="flex items-start gap-3 rounded-md border border-line p-3 transition-colors hover:border-clinical hover:bg-clinical/5"
                  href={card.href}
                  key={card.href}
                >
                  <span className="mt-0.5 text-base" aria-hidden="true">
                    {card.icon}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-ink">{card.title}</p>
                    <p className="mt-0.5 text-xs leading-5 text-graphite">
                      {card.text}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}
