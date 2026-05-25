"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { FailureDistributionChart } from "@/components/charts/failure-distribution-chart";
import { MetricBarChart } from "@/components/charts/metric-bar-chart";
import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate, formatMetric, formatNumber, truncate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type {
  Experiment,
  ExperimentResponseRow,
  ExperimentResults,
} from "@/types/experiments";

export default function ExperimentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  // All hooks must come before any conditional returns
  const experiment = useApi<Experiment>(id ? `/experiments/${id}` : null);
  const results = useApi<ExperimentResults>(
    id ? `/experiments/${id}/results` : null,
  );
  const responses = useApi<ExperimentResponseRow[]>(
    id ? `/experiments/${id}/responses` : null,
  );
  const [failureFilter, setFailureFilter] = useState("all");
  const [answerabilityFilter, setAnswerabilityFilter] = useState("all");
  const [hallucinationFilter, setHallucinationFilter] = useState("all");

  const filteredResponses = useMemo(() => {
    return (responses.data ?? []).filter((response) => {
      const failure = response.failure_type || "none";
      const hallucination = response.hallucination_flag ? "flagged" : "not_flagged";
      return (
        (failureFilter === "all" || failure === failureFilter) &&
        (answerabilityFilter === "all" ||
          response.expected_answerability === answerabilityFilter) &&
        (hallucinationFilter === "all" || hallucination === hallucinationFilter)
      );
    });
  }, [answerabilityFilter, failureFilter, hallucinationFilter, responses.data]);

  const failureOptions = useMemo(
    () =>
      Array.from(
        new Set(
          (responses.data ?? []).map((r) => r.failure_type || "none"),
        ),
      ).sort(),
    [responses.data],
  );
  const answerabilityOptions = useMemo(
    () =>
      Array.from(
        new Set((responses.data ?? []).map((r) => r.expected_answerability)),
      ).sort(),
    [responses.data],
  );

  if (experiment.loading || results.loading || responses.loading) {
    return <LoadingState label="Loading experiment..." />;
  }
  if (experiment.error) {
    return <ErrorState message={experiment.error} />;
  }
  if (!experiment.data) {
    return (
      <EmptyState
        title="Experiment not found"
        message="The backend did not return this experiment."
        showSeedCommands={false}
      />
    );
  }

  const metricData = [
    { name: "Correct", value: results.data?.avg_correctness ?? 0 },
    { name: "Grounded", value: results.data?.avg_groundedness ?? 0 },
    { name: "Cit P", value: results.data?.avg_citation_precision ?? 0 },
    { name: "Cit R", value: results.data?.avg_citation_recall ?? 0 },
    { name: "Ret R", value: results.data?.avg_retrieval_recall ?? 0 },
    { name: "Refusal", value: results.data?.refusal_accuracy ?? 0 },
  ];

  const hallucinationRate = results.data?.hallucination_rate;

  return (
    <>
      <PageHeader
        title={experiment.data.name}
        description="Configuration, aggregate evaluation metrics, failure distribution, and per-response traces."
        action={
          <Link
            className="inline-flex items-center gap-1.5 rounded-md bg-clinical px-4 py-2 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-90"
            href={`/experiments/${id}/report`}
          >
            View report →
          </Link>
        }
      />

      {/* Aggregate metrics */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Status"
          value={experiment.data.status}
          accent={
            experiment.data.status === "completed"
              ? "success"
              : experiment.data.status === "failed"
                ? "danger"
                : undefined
          }
        />
        <MetricCard
          label="Examples evaluated"
          value={formatNumber(results.data?.example_count)}
        />
        <MetricCard
          label="Avg correctness"
          value={formatMetric(results.data?.avg_correctness)}
          accent={
            results.data?.avg_correctness != null
              ? results.data.avg_correctness >= 0.75
                ? "success"
                : results.data.avg_correctness >= 0.5
                  ? "warning"
                  : "danger"
              : undefined
          }
        />
        <MetricCard
          label="Hallucination rate"
          value={formatMetric(hallucinationRate)}
          accent={
            hallucinationRate != null
              ? hallucinationRate > 0.3
                ? "danger"
                : hallucinationRate > 0.1
                  ? "warning"
                  : "success"
              : undefined
          }
        />
        <MetricCard
          label="Avg groundedness"
          value={formatMetric(results.data?.avg_groundedness)}
          accent={
            results.data?.avg_groundedness != null
              ? results.data.avg_groundedness >= 0.75
                ? "success"
                : results.data.avg_groundedness >= 0.5
                  ? "warning"
                  : "danger"
              : undefined
          }
        />
        <MetricCard
          label="Citation precision"
          value={formatMetric(results.data?.avg_citation_precision)}
        />
        <MetricCard
          label="Citation recall"
          value={formatMetric(results.data?.avg_citation_recall)}
        />
        <MetricCard
          label="Retrieval recall"
          value={formatMetric(results.data?.avg_retrieval_recall)}
        />
      </div>

      {/* Charts */}
      <section className="mt-5 grid gap-5 lg:grid-cols-2">
        <MetricBarChart
          data={metricData}
          title="Evaluation Scores Overview"
        />
        <FailureDistributionChart
          counts={results.data?.failure_type_counts ?? {}}
          title="Failure Type Distribution"
        />
      </section>

      {/* Configuration */}
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-graphite">
          Configuration
        </h2>
        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
          {[
            ["Provider", experiment.data.model_provider],
            ["Model", experiment.data.model_name],
            ["Embedding model", experiment.data.embedding_model],
            ["Retrieval strategy", experiment.data.retrieval_strategy],
            ["Top-k", String(experiment.data.top_k)],
            ["Temperature", String(experiment.data.temperature)],
            ["Created", formatDate(experiment.data.created_at)],
          ].map(([label, val]) => (
            <div key={label} className="flex gap-1.5">
              <span className="shrink-0 font-medium text-ink">{label}:</span>
              <span className="text-graphite font-mono text-xs mt-0.5">{val}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Response traces */}
      <section className="mt-5 overflow-hidden rounded-lg border border-line bg-white shadow-sm">
        <div className="border-b border-line bg-surface/50 px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-ink">
              Model responses
              {responses.data?.length ? (
                <span className="ml-2 rounded-full bg-white px-2 py-0.5 text-xs font-medium text-graphite border border-line">
                  {filteredResponses.length} / {responses.data.length}
                </span>
              ) : null}
            </h2>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <select
              className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink focus:border-clinical focus:outline-none"
              onChange={(event) => setFailureFilter(event.target.value)}
              value={failureFilter}
            >
              <option value="all">All failure types</option>
              {failureOptions.map((failure) => (
                <option key={failure} value={failure}>
                  {failure}
                </option>
              ))}
            </select>
            <select
              className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink focus:border-clinical focus:outline-none"
              onChange={(event) => setAnswerabilityFilter(event.target.value)}
              value={answerabilityFilter}
            >
              <option value="all">All answerability</option>
              {answerabilityOptions.map((answerability) => (
                <option key={answerability} value={answerability}>
                  {answerability}
                </option>
              ))}
            </select>
            <select
              className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink focus:border-clinical focus:outline-none"
              onChange={(event) => setHallucinationFilter(event.target.value)}
              value={hallucinationFilter}
            >
              <option value="all">All hallucination states</option>
              <option value="flagged">Hallucination flagged</option>
              <option value="not_flagged">Not flagged</option>
            </select>
          </div>
        </div>

        {responses.error ? <ErrorState message={responses.error} /> : null}
        {responses.data?.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="No responses"
              message="Run this experiment to generate response traces."
              showSeedCommands={false}
            />
          </div>
        ) : null}
        {responses.data?.length && filteredResponses.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="No matching responses"
              message="Adjust the filters to see more response traces."
              showSeedCommands={false}
            />
          </div>
        ) : null}

        {filteredResponses.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead className="border-b border-line bg-surface">
                <tr>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Question
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Answerability
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Correctness
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Groundedness
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Failure type
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                    Hallucination
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {filteredResponses.map((response) => (
                  <tr
                    className="align-top transition-colors hover:bg-surface/60"
                    key={response.response_id}
                  >
                    <td className="max-w-xs px-4 py-3.5 font-medium">
                      <Link
                        className="text-clinical hover:underline"
                        href={`/traces/${response.response_id}`}
                      >
                        {truncate(response.question, 110)}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5">
                      <StatusBadge value={response.expected_answerability} />
                    </td>
                    <td className="px-4 py-3.5 tabular-nums text-sm">
                      {formatMetric(response.correctness_score)}
                    </td>
                    <td className="px-4 py-3.5 tabular-nums text-sm">
                      {formatMetric(response.groundedness_score)}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-col gap-1">
                        <StatusBadge value={response.failure_type || "none"} />
                        {response.failure_reason ? (
                          <span className="text-xs text-graphite">
                            {truncate(response.failure_reason, 80)}
                          </span>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      {response.hallucination_flag ? (
                        <span className="inline-flex items-center gap-1 rounded-full border border-danger/30 bg-danger/10 px-2.5 py-0.5 text-xs font-medium text-danger">
                          ⚑ Flagged
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full border border-success/30 bg-success/10 px-2.5 py-0.5 text-xs font-medium text-success">
                          ✓ Clean
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <div className="mt-5">
        <DisclaimerCallout
          message="These are deterministic evaluation results from locally seeded synthetic data. Scores are not validated benchmark results and should not be compared to clinical ground truth or published benchmarks."
          compact
        />
      </div>
    </>
  );
}
