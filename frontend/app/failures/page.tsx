"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { FailureDistributionChart } from "@/components/charts/failure-distribution-chart";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { truncate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { Experiment, ExperimentFailureRow } from "@/types/experiments";

export default function FailuresPage() {
  const experiments = useApi<Experiment[]>("/experiments");
  const latestCompleted = useMemo(
    () => experiments.data?.find((experiment) => experiment.status === "completed") ?? experiments.data?.[0],
    [experiments.data],
  );
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(null);
  const activeExperimentId = selectedExperimentId ?? latestCompleted?.id ?? null;
  const failures = useApi<ExperimentFailureRow[]>(
    activeExperimentId ? `/experiments/${activeExperimentId}/failures` : null,
  );
  const counts = (failures.data ?? []).reduce<Record<string, number>>((accumulator, failure) => {
    const key = failure.failure_type || "flagged";
    accumulator[key] = (accumulator[key] ?? 0) + 1;
    return accumulator;
  }, {});

  return (
    <>
      <PageHeader
        title="Failure Analysis"
        description="Review failed refusals, hallucination flags, citation problems, and retrieval misses by experiment."
        action={
          experiments.data?.length ? (
            <select
              className="rounded-md border border-line bg-white px-3 py-2 text-sm"
              onChange={(event) => setSelectedExperimentId(event.target.value)}
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
      {experiments.loading || failures.loading ? <LoadingState label="Loading failures..." /> : null}
      {experiments.error ? <ErrorState message={experiments.error} /> : null}
      {failures.error ? <ErrorState message={failures.error} /> : null}
      {!activeExperimentId ? (
        <EmptyState title="No experiments available" message="Run a sample experiment to inspect failures." />
      ) : null}
      {activeExperimentId && failures.data?.length === 0 ? (
        <EmptyState
          title="No failures found"
          message="This experiment has no failure rows from the MVP evaluator."
        />
      ) : null}
      {failures.data?.length ? (
        <>
          <FailureDistributionChart counts={counts} />
          <div className="mt-5 overflow-hidden rounded-lg border border-line bg-white shadow-sm">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="bg-surface text-xs uppercase text-graphite">
                <tr>
                  <th className="px-4 py-3">Question</th>
                  <th className="px-4 py-3">Failure</th>
                  <th className="px-4 py-3">Expected</th>
                  <th className="px-4 py-3">Answer</th>
                </tr>
              </thead>
              <tbody>
                {failures.data.map((failure) => (
                  <tr className="border-t border-line align-top" key={failure.response_id}>
                    <td className="px-4 py-3 font-medium">
                      <Link className="text-clinical hover:underline" href={`/traces/${failure.response_id}`}>
                        {truncate(failure.question, 120)}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1">
                        <StatusBadge value={failure.primary_failure_type || failure.failure_type} />
                        {failure.failure_reason ? (
                          <span className="text-xs text-graphite">{truncate(failure.failure_reason, 90)}</span>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-4 py-3">{failure.expected_answerability}</td>
                    <td className="px-4 py-3 text-graphite">{truncate(failure.answer_text, 140)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </>
  );
}
