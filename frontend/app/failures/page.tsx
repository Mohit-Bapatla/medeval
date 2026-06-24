"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { FailureDistributionChart } from "@/components/charts/failure-distribution-chart";
import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { truncate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { Experiment, ExperimentFailureRow } from "@/types/experiments";

export default function FailuresPage() {
  const experiments = useApi<Experiment[]>("/experiments");
  const latestCompleted = useMemo(
    () =>
      experiments.data?.find(
        (experiment) => experiment.status === "completed",
      ) ?? experiments.data?.[0],
    [experiments.data],
  );
  const [selectedExperimentId, setSelectedExperimentId] = useState<
    string | null
  >(null);
  const activeExperimentId =
    selectedExperimentId ?? latestCompleted?.id ?? null;
  const failures = useApi<ExperimentFailureRow[]>(
    activeExperimentId
      ? `/experiments/${activeExperimentId}/failures`
      : null,
  );

  const counts = (failures.data ?? []).reduce<Record<string, number>>(
    (accumulator, failure) => {
      const key = failure.failure_type || "flagged";
      accumulator[key] = (accumulator[key] ?? 0) + 1;
      return accumulator;
    },
    {},
  );

  const totalFailures = failures.data?.length ?? 0;
  const hallucinationCount = (failures.data ?? []).filter(
    (f) =>
      f.primary_failure_type?.includes("hallucinat") ||
      f.failure_type?.includes("hallucinat"),
  ).length;
  const citationCount = (failures.data ?? []).filter(
    (f) =>
      f.primary_failure_type?.includes("citation") ||
      f.failure_type?.includes("citation"),
  ).length;
  const retrievalCount = (failures.data ?? []).filter(
    (f) =>
      f.primary_failure_type?.includes("retrieval") ||
      f.failure_type?.includes("retrieval"),
  ).length;

  return (
    <>
      <PageHeader
        title="Failure Analysis"
        description="Failed refusals, hallucination flags, citation problems, and retrieval misses — reviewed by failure type across experiments."
        action={
          experiments.data?.length ? (
            <select
              className="rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-ink focus:border-clinical focus:outline-none shadow-sm"
              onChange={(event) =>
                setSelectedExperimentId(event.target.value)
              }
              value={activeExperimentId ?? ""}
            >
              {experiments.data.map((experiment) => (
                <option key={experiment.id} value={experiment.id}>
                  {experiment.name}
                </option>
              ))}
            </select>
          ) : null
        }
      />

      {experiments.loading || failures.loading ? (
        <LoadingState label="Loading failure data..." />
      ) : null}
      {experiments.error ? <ErrorState message={experiments.error} /> : null}
      {failures.error ? <ErrorState message={failures.error} /> : null}

      {!activeExperimentId ? (
        <EmptyState
          title="No experiments available"
          message="Run a sample experiment to inspect failure patterns."
        />
      ) : null}

      {activeExperimentId && failures.data?.length === 0 ? (
        <EmptyState
          title="No failures found"
          message="This experiment produced no failure rows from the MVP evaluator."
          showSeedCommands={false}
        />
      ) : null}

      {failures.data?.length ? (
        <>
          {/* Summary counts */}
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 mb-5">
            <MetricCard
              label="Total failures"
              value={totalFailures}
              accent="danger"
            />
            <MetricCard
              label="Hallucinations"
              value={hallucinationCount}
              accent={hallucinationCount > 0 ? "danger" : "success"}
            />
            <MetricCard
              label="Citation failures"
              value={citationCount}
              accent={citationCount > 0 ? "warning" : "success"}
            />
            <MetricCard
              label="Retrieval misses"
              value={retrievalCount}
              accent={retrievalCount > 0 ? "warning" : "success"}
            />
          </div>

          {/* Chart + table layout */}
          <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
            <FailureDistributionChart
              counts={counts}
              title="Failure breakdown"
            />

            <div className="overflow-x-auto rounded-lg border border-line bg-white shadow-sm">
              <div className="border-b border-line bg-surface/50 px-4 py-3">
                <p className="text-sm font-semibold text-ink">
                  Failure rows
                  <span className="ml-2 rounded-full border border-line bg-white px-2 py-0.5 text-xs font-medium text-graphite">
                    {totalFailures}
                  </span>
                </p>
                <p className="mt-0.5 text-xs text-graphite">
                  Click a question to open the full trace viewer.
                </p>
              </div>
              <table className="w-full min-w-[600px] border-collapse text-left text-sm">
                <thead className="border-b border-line bg-surface">
                  <tr>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                      Question
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                      Failure type
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                      Expected
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                      Answer preview
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {failures.data.map((failure) => (
                    <tr
                      className="align-top transition-colors hover:bg-surface/60"
                      key={failure.response_id}
                    >
                      <td className="max-w-xs px-4 py-3.5 font-medium">
                        <Link
                          className="text-clinical hover:underline"
                          href={`/traces/${failure.response_id}`}
                        >
                          {truncate(failure.question, 110)}
                        </Link>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex flex-col gap-1">
                          <StatusBadge
                            value={
                              failure.primary_failure_type ||
                              failure.failure_type
                            }
                          />
                          {failure.failure_reason ? (
                            <span className="text-xs text-graphite">
                              {truncate(failure.failure_reason, 80)}
                            </span>
                          ) : null}
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <StatusBadge value={failure.expected_answerability} />
                      </td>
                      <td className="max-w-xs px-4 py-3.5 text-sm text-graphite">
                        {truncate(failure.answer_text, 120)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-5">
            <DisclaimerCallout
              message="These failure rows are produced by deterministic local evaluators over seeded data. Failure labels are heuristic diagnostics calibrated by self-review labels, not clinical validation."
              compact
            />
          </div>
        </>
      ) : null}
    </>
  );
}
