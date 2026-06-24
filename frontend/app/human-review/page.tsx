"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiFetch } from "@/lib/api";
import { formatMetric, truncate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { Experiment } from "@/types/experiments";
import type {
  ManualReviewSnapshot,
  ReviewQueue,
  ReviewQueueItem,
  ReviewStatus,
  ReviewSummary,
  ReviewerType,
} from "@/types/human-review";

type TriState = "unknown" | "yes" | "no";

type ReviewFormState = {
  reviewer_label: string;
  reviewer_type: ReviewerType;
  review_status: ReviewStatus;
  answer_correctness: string;
  groundedness: string;
  citation_quality: string;
  refusal_safety: string;
  should_refuse: TriState;
  did_refuse: TriState;
  selected_failure_categories: string[];
  severity_override: string;
  confidence: string;
  reviewer_time_seconds: string;
  adjudication_status: "none" | "needs_second_review" | "adjudicated";
  review_notes: string;
  sample: boolean;
};

const FAILURE_CATEGORIES = [
  "retrieval_miss",
  "retrieval_rank_failure",
  "context_overload",
  "unsupported_claim",
  "citation_mismatch",
  "missing_citation",
  "incomplete_answer",
  "over_answering",
  "failed_refusal",
  "over_refusal",
  "ambiguity_failure",
  "temporal_failure",
  "contradiction",
  "bad_synthesis",
  "format_failure",
];

const SCORE_OPTIONS = ["", "1", "2", "3", "4", "5"];

function labelize(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function reviewStatus(item: ReviewQueueItem): ReviewStatus {
  const status = item.manual_review?.review_status;
  if (status === "completed" || status === "skipped") {
    return status;
  }
  return "pending";
}

function scoreToString(value?: number | null): string {
  return value == null ? "" : String(value);
}

function boolToTri(value?: boolean | null): TriState {
  if (value == null) return "unknown";
  return value ? "yes" : "no";
}

function triToBool(value: TriState): boolean | null {
  if (value === "unknown") return null;
  return value === "yes";
}

function scoreFromInput(value: string): number | null {
  if (!value) return null;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 5) {
    throw new Error("Rubric scores must be integers from 1 to 5.");
  }
  return parsed;
}

function formFromReview(review?: ManualReviewSnapshot | null): ReviewFormState {
  return {
    reviewer_label: review?.reviewer_label || "local_reviewer",
    reviewer_type:
      review?.reviewer_type === "self" ||
      review?.reviewer_type === "student" ||
      review?.reviewer_type === "domain_reviewer" ||
      review?.reviewer_type === "clinician"
        ? review.reviewer_type
        : "unknown",
    review_status:
      review?.review_status === "pending" || review?.review_status === "skipped"
        ? review.review_status
        : "completed",
    answer_correctness: scoreToString(review?.answer_correctness),
    groundedness: scoreToString(review?.groundedness),
    citation_quality: scoreToString(review?.citation_quality),
    refusal_safety: scoreToString(review?.refusal_safety),
    should_refuse: boolToTri(review?.should_refuse),
    did_refuse: boolToTri(review?.did_refuse),
    selected_failure_categories: review?.selected_failure_categories ?? [],
    severity_override: review?.severity_override ?? "",
    confidence: scoreToString(review?.confidence),
    reviewer_time_seconds:
      review?.reviewer_time_seconds == null ? "" : String(review.reviewer_time_seconds),
    adjudication_status:
      review?.adjudication_status === "needs_second_review" ||
      review?.adjudication_status === "adjudicated"
        ? review.adjudication_status
        : "none",
    review_notes: review?.review_notes ?? "",
    sample: review?.sample ?? false,
  };
}

function scoreFive(value?: number | null): string {
  return value == null ? "n/a" : `${value.toFixed(1)}/5`;
}

function countByStatus(items: ReviewQueueItem[], status: ReviewStatus): number {
  return items.filter((item) => reviewStatus(item) === status).length;
}

function scoreClass(value?: number | null): "danger" | "success" | "warning" | undefined {
  if (value == null) return undefined;
  if (value >= 4) return "success";
  if (value >= 3) return "warning";
  return "danger";
}

function statusStyle(status: ReviewStatus): string {
  if (status === "completed") {
    return "border-success/40 bg-success/5";
  }
  if (status === "skipped") {
    return "border-signal/40 bg-signal/5";
  }
  return "border-line bg-white";
}

export default function HumanReviewPage() {
  const experiments = useApi<Experiment[]>("/experiments");
  const [experimentId, setExperimentId] = useState("");
  const [selectedResponseId, setSelectedResponseId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | ReviewStatus>("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [safetyOnly, setSafetyOnly] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [form, setForm] = useState<ReviewFormState>(() => formFromReview(null));
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = params.get("experiment_id");
    if (fromUrl) {
      setExperimentId(fromUrl);
    }
  }, []);

  useEffect(() => {
    if (!experimentId && experiments.data?.length) {
      setExperimentId(experiments.data[0].id);
    }
  }, [experimentId, experiments.data]);

  const encodedExperimentId = experimentId ? encodeURIComponent(experimentId) : "";
  const queue = useApi<ReviewQueue>(
    encodedExperimentId
      ? `/human-reviews/queue?experiment_id=${encodedExperimentId}`
      : null,
  );
  const summary = useApi<ReviewSummary>(
    encodedExperimentId
      ? `/human-reviews/summary?experiment_id=${encodedExperimentId}`
      : null,
  );

  const selectedItem = useMemo(
    () =>
      queue.data?.items.find((item) => item.response_id === selectedResponseId) ??
      queue.data?.items[0] ??
      null,
    [queue.data?.items, selectedResponseId],
  );

  const detail = useApi<ReviewQueueItem>(
    selectedItem ? `/human-reviews/responses/${selectedItem.response_id}/detail` : null,
  );

  useEffect(() => {
    if (!queue.data?.items.length) {
      setSelectedResponseId(null);
      return;
    }
    if (!selectedResponseId || !queue.data.items.some((item) => item.response_id === selectedResponseId)) {
      setSelectedResponseId(queue.data.items[0].response_id);
    }
  }, [queue.data?.items, selectedResponseId]);

  const activeItem = detail.data ?? selectedItem;

  useEffect(() => {
    setForm(formFromReview(activeItem?.manual_review));
    setSaveMessage(null);
    setSaveError(null);
  }, [activeItem?.response_id, activeItem?.manual_review?.review_id]);

  const summaryRowsByResponse = useMemo(() => {
    const rows = new Map<string, ReviewSummary["rows"][number]>();
    for (const row of summary.data?.rows ?? []) {
      rows.set(row.response_id, row);
    }
    return rows;
  }, [summary.data?.rows]);

  const severityOptions = useMemo(() => {
    const severities = new Set<string>();
    for (const item of queue.data?.items ?? []) {
      const severity = item.rich_failure_taxonomy?.severity;
      if (severity) {
        severities.add(String(severity));
      }
    }
    return Array.from(severities).sort();
  }, [queue.data?.items]);

  const filteredItems = useMemo(() => {
    const query = searchText.trim().toLowerCase();
    return (queue.data?.items ?? []).filter((item) => {
      const taxonomy = item.rich_failure_taxonomy;
      const status = reviewStatus(item);
      const searchable = `${item.question} ${item.generated_answer} ${item.qa_id ?? ""}`.toLowerCase();
      return (
        (statusFilter === "all" || status === statusFilter) &&
        (severityFilter === "all" || taxonomy?.severity === severityFilter) &&
        (!safetyOnly || taxonomy?.safety_relevant_failure === true) &&
        (!query || searchable.includes(query))
      );
    });
  }, [queue.data?.items, safetyOnly, searchText, severityFilter, statusFilter]);

  function refreshReviewData() {
    queue.reload();
    summary.reload();
    detail.reload();
  }

  function toggleCategory(category: string) {
    setForm((current) => ({
      ...current,
      selected_failure_categories: current.selected_failure_categories.includes(category)
        ? current.selected_failure_categories.filter((item) => item !== category)
        : [...current.selected_failure_categories, category],
    }));
  }

  async function saveReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeItem) {
      return;
    }
    setSaveMessage(null);
    setSaveError(null);
    setSaving(true);
    try {
      const reviewerSeconds = form.reviewer_time_seconds
        ? Number(form.reviewer_time_seconds)
        : null;
      if (reviewerSeconds != null && (!Number.isInteger(reviewerSeconds) || reviewerSeconds < 0)) {
        throw new Error("Reviewer time must be a non-negative integer.");
      }
      await apiFetch(`/human-reviews/responses/${activeItem.response_id}`, {
        method: "PUT",
        body: JSON.stringify({
          reviewer_label: form.reviewer_label.trim() || "local_reviewer",
          reviewer_type: form.reviewer_type,
          review_status: form.review_status,
          answer_correctness: scoreFromInput(form.answer_correctness),
          groundedness: scoreFromInput(form.groundedness),
          citation_quality: scoreFromInput(form.citation_quality),
          refusal_safety: scoreFromInput(form.refusal_safety),
          should_refuse: triToBool(form.should_refuse),
          did_refuse: triToBool(form.did_refuse),
          selected_failure_categories: form.selected_failure_categories,
          severity_override: form.severity_override || null,
          review_notes: form.review_notes.trim() || null,
          confidence: scoreFromInput(form.confidence),
          reviewer_time_seconds: reviewerSeconds,
          adjudication_status: form.adjudication_status,
          sample: form.sample,
          sample_notes: form.sample
            ? "Marked as sample fixture or workflow test in the dashboard."
            : null,
        }),
      });
      setSaveMessage("Review saved. Queue and calibration summary refreshed.");
      refreshReviewData();
    } catch (caught) {
      setSaveError(caught instanceof Error ? caught.message : "Unable to save review.");
    } finally {
      setSaving(false);
    }
  }

  const items = queue.data?.items ?? [];
  const completedCount = countByStatus(items, "completed");
  const pendingCount = countByStatus(items, "pending");
  const skippedCount = countByStatus(items, "skipped");
  const commonCategories = Object.entries(summary.data?.reviewer_failure_category_counts ?? {})
    .sort((left, right) => right[1] - left[1])
    .slice(0, 5);
  const sampleWarning =
    activeItem?.manual_review?.sample ||
    form.sample ||
    form.reviewer_label.toLowerCase().includes("sample_fixture_reviewer");

  return (
    <>
      <PageHeader
        title="Human Review"
        description="Review MedEval experiment outputs, compare reviewer labels against automated diagnostics, and export calibration summaries."
      />

      <div className="grid gap-5">
        <DisclaimerCallout message="This is a manual review workflow only. It is not clinical validation, not medical advice, and not evidence of clinician review unless the reviewer_type is explicitly clinician. Sample fixtures are workflow examples, not real independent review." />

        <section className="rounded-lg border border-line bg-white p-4 shadow-sm">
          <div className="grid gap-3 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
            <label className="grid gap-1.5 text-sm">
              <span className="text-xs font-semibold uppercase tracking-wide text-graphite">
                Experiment
              </span>
              <select
                className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                disabled={experiments.loading || !experiments.data?.length}
                onChange={(event) => setExperimentId(event.target.value)}
                value={experimentId}
              >
                <option value="">Select an experiment</option>
                {(experiments.data ?? []).map((experiment) => (
                  <option key={experiment.id} value={experiment.id}>
                    {experiment.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1.5 text-sm">
              <span className="text-xs font-semibold uppercase tracking-wide text-graphite">
                Direct experiment id
              </span>
              <input
                className="rounded-md border border-line bg-white px-3 py-2 font-mono text-xs text-ink"
                onChange={(event) => setExperimentId(event.target.value.trim())}
                placeholder="UUID"
                value={experimentId}
              />
            </label>
            <button
              className="rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-clinical hover:bg-white"
              onClick={refreshReviewData}
              type="button"
            >
              Refresh
            </button>
          </div>
        </section>

        {queue.loading || summary.loading ? <LoadingState label="Loading review workflow..." /> : null}
        {queue.error ? <ErrorState message={queue.error} /> : null}
        {summary.error ? <ErrorState message={summary.error} /> : null}

        {queue.data ? (
          <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Reviewable responses" value={items.length} />
              <MetricCard
                label="Completed"
                value={completedCount}
                helper={`${pendingCount} pending, ${skippedCount} skipped`}
                accent={completedCount ? "success" : undefined}
              />
              <MetricCard
                label="Avg correctness"
                value={scoreFive(summary.data?.rubric_averages.answer_correctness)}
                helper="Completed reviews only"
                accent={scoreClass(summary.data?.rubric_averages.answer_correctness)}
              />
              <MetricCard
                label="Avg groundedness"
                value={scoreFive(summary.data?.rubric_averages.groundedness)}
                helper="Completed reviews only"
                accent={scoreClass(summary.data?.rubric_averages.groundedness)}
              />
              <MetricCard
                label="Avg citation"
                value={scoreFive(summary.data?.rubric_averages.citation_quality)}
                helper="Completed reviews only"
              />
              <MetricCard
                label="Avg refusal safety"
                value={scoreFive(summary.data?.rubric_averages.refusal_safety)}
                helper="Completed reviews only"
              />
              <MetricCard
                label="Category Jaccard"
                value={formatMetric(Number(summary.data?.calibration.avg_category_jaccard ?? NaN))}
                helper={`${summary.data?.calibration.exact_category_match_count ?? 0} exact category matches`}
              />
              <MetricCard
                label="Refusal agreement"
                value={formatMetric(
                  Number(summary.data?.calibration.refusal_decision_agreement_rate ?? NaN),
                )}
                helper={`${summary.data?.calibration.severity_match_count ?? 0} severity matches`}
              />
            </section>

            <section className="rounded-lg border border-line bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-graphite">
                    Reviewer categories
                  </p>
                  <p className="mt-1 text-sm text-graphite">
                    {summary.data?.completed_review_count
                      ? `${summary.data.completed_review_count} completed review(s), ${summary.data.reviewer_override_count} reviewer override(s).`
                      : "No completed manual reviews yet. This is expected for a fresh experiment."}
                  </p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {commonCategories.length ? (
                    commonCategories.map(([category, count]) => (
                      <span
                        className="rounded-full border border-line bg-surface px-2.5 py-1 text-xs text-graphite"
                        key={category}
                      >
                        {category}: {count}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-graphite">
                      No reviewer-selected categories yet.
                    </span>
                  )}
                </div>
              </div>
            </section>

            <div className="grid gap-5 xl:grid-cols-[430px_1fr]">
              <section className="rounded-lg border border-line bg-white shadow-sm">
                <div className="border-b border-line bg-surface/60 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="text-sm font-semibold text-ink">Review queue</h2>
                    <span className="rounded-full border border-line bg-white px-2 py-0.5 text-xs text-graphite">
                      {filteredItems.length} / {items.length}
                    </span>
                  </div>
                  <div className="mt-3 grid gap-2">
                    <input
                      className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                      onChange={(event) => setSearchText(event.target.value)}
                      placeholder="Search questions or answers"
                      value={searchText}
                    />
                    <div className="grid gap-2 sm:grid-cols-2">
                      <select
                        className="rounded-md border border-line bg-white px-3 py-2 text-xs text-ink"
                        onChange={(event) =>
                          setStatusFilter(event.target.value as "all" | ReviewStatus)
                        }
                        value={statusFilter}
                      >
                        <option value="all">All statuses</option>
                        <option value="pending">Pending</option>
                        <option value="completed">Completed</option>
                        <option value="skipped">Skipped</option>
                      </select>
                      <select
                        className="rounded-md border border-line bg-white px-3 py-2 text-xs text-ink"
                        onChange={(event) => setSeverityFilter(event.target.value)}
                        value={severityFilter}
                      >
                        <option value="all">All severities</option>
                        {severityOptions.map((severity) => (
                          <option key={severity} value={severity}>
                            {severity}
                          </option>
                        ))}
                      </select>
                    </div>
                    <label className="flex items-center gap-2 text-xs text-graphite">
                      <input
                        checked={safetyOnly}
                        onChange={(event) => setSafetyOnly(event.target.checked)}
                        type="checkbox"
                      />
                      Safety-relevant diagnostics only
                    </label>
                  </div>
                </div>
                <div className="max-h-[760px] overflow-y-auto p-3">
                  {filteredItems.length ? (
                    <div className="grid gap-2">
                      {filteredItems.map((item) => {
                        const status = reviewStatus(item);
                        const summaryRow = summaryRowsByResponse.get(item.response_id);
                        return (
                          <button
                            className={`rounded-lg border p-3 text-left transition-colors hover:border-clinical ${statusStyle(status)} ${
                              activeItem?.response_id === item.response_id
                                ? "ring-2 ring-clinical/25"
                                : ""
                            }`}
                            key={item.response_id}
                            onClick={() => setSelectedResponseId(item.response_id)}
                            type="button"
                          >
                            <div className="flex flex-wrap items-center gap-1.5">
                              <StatusBadge value={status} />
                              <StatusBadge value={item.rich_failure_taxonomy?.severity ?? "none"} />
                              {item.rich_failure_taxonomy?.safety_relevant_failure ? (
                                <StatusBadge value="safety" />
                              ) : null}
                              {item.manual_review?.sample ? <StatusBadge value="sample" /> : null}
                            </div>
                            <p className="mt-2 text-sm font-semibold leading-5 text-ink">
                              {item.question}
                            </p>
                            <p className="mt-1 text-xs leading-5 text-graphite">
                              {truncate(item.generated_answer, 180)}
                            </p>
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              <StatusBadge value={item.legacy_failure_type ?? "none"} />
                              {(item.rich_failure_taxonomy?.failure_categories ?? [])
                                .slice(0, 3)
                                .map((category) => (
                                  <span
                                    className="rounded-full border border-line bg-white px-2 py-0.5 text-[11px] text-graphite"
                                    key={category}
                                  >
                                    {category}
                                  </span>
                                ))}
                            </div>
                            {summaryRow ? (
                              <p className="mt-2 text-xs text-graphite">
                                Manual: correctness {summaryRow.answer_correctness ?? "n/a"},
                                groundedness {summaryRow.groundedness ?? "n/a"},
                                Jaccard {summaryRow.category_jaccard?.toFixed(2) ?? "n/a"}
                              </p>
                            ) : null}
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <EmptyState
                      title="No queue items match"
                      message="Adjust filters or choose a different experiment."
                      showSeedCommands={false}
                    />
                  )}
                </div>
              </section>

              <section className="grid gap-5 content-start">
                {!activeItem ? (
                  <EmptyState
                    title="No response selected"
                    message="Choose an experiment response to inspect automated diagnostics and enter a review."
                    showSeedCommands={false}
                  />
                ) : (
                  <>
                    {detail.loading ? <LoadingState label="Loading response detail..." /> : null}
                    {detail.error ? <ErrorState message={detail.error} /> : null}

                    {sampleWarning ? (
                      <DisclaimerCallout
                        compact
                        message="This selected record is marked as a sample fixture or uses the sample fixture reviewer label. Do not interpret it as real independent human review."
                      />
                    ) : null}

                    <div className="rounded-lg border border-line bg-white shadow-sm">
                      <div className="border-b border-line bg-surface/60 p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-graphite">
                              Response detail
                            </p>
                            <h2 className="mt-1 text-lg font-bold leading-6 text-ink">
                              {activeItem.question}
                            </h2>
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            <StatusBadge value={activeItem.expected_answerability} />
                            <StatusBadge value={`model: ${activeItem.model_answerability}`} />
                          </div>
                        </div>
                      </div>
                      <div className="grid gap-4 p-4 lg:grid-cols-2">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-success">
                            Gold answer
                          </p>
                          <p className="mt-2 text-sm leading-6 text-graphite">
                            {activeItem.gold_answer || "No gold answer available."}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-clinical">
                            Generated answer
                          </p>
                          <p className="mt-2 text-sm leading-6 text-graphite">
                            {activeItem.generated_answer}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                      <MetricCard
                        label="Correctness"
                        value={formatMetric(activeItem.automated_scores.correctness_score)}
                      />
                      <MetricCard
                        label="Groundedness"
                        value={formatMetric(activeItem.automated_scores.groundedness_score)}
                      />
                      <MetricCard
                        label="Citation precision"
                        value={formatMetric(activeItem.automated_scores.citation_precision)}
                      />
                      <MetricCard
                        label="Retrieval recall"
                        value={formatMetric(activeItem.automated_scores.retrieval_recall)}
                      />
                    </div>

                    <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-graphite">
                          Automated diagnostics
                        </p>
                        <StatusBadge value={activeItem.legacy_failure_type ?? "none"} />
                        <StatusBadge
                          value={activeItem.rich_failure_taxonomy?.failure_stage ?? "no stage"}
                        />
                        <StatusBadge value={activeItem.rich_failure_taxonomy?.severity ?? "none"} />
                        {activeItem.rich_failure_taxonomy?.safety_relevant_failure ? (
                          <StatusBadge value="safety relevant" />
                        ) : null}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {(activeItem.rich_failure_taxonomy?.failure_categories ?? []).length ? (
                          activeItem.rich_failure_taxonomy?.failure_categories?.map((category) => (
                            <span
                              className="rounded-full border border-line bg-surface px-2.5 py-1 text-xs text-graphite"
                              key={category}
                            >
                              {category}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-graphite">
                            No rich failure categories assigned.
                          </span>
                        )}
                      </div>
                      {(activeItem.rich_failure_taxonomy?.diagnostic_notes ?? []).length ? (
                        <ul className="mt-3 grid gap-1 text-sm leading-6 text-graphite">
                          {activeItem.rich_failure_taxonomy?.diagnostic_notes?.map((note) => (
                            <li key={note}>{note}</li>
                          ))}
                        </ul>
                      ) : null}
                    </div>

                    <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
                      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                        <h2 className="text-sm font-semibold uppercase tracking-wide text-graphite">
                          Retrieved and cited chunks
                        </h2>
                        <span className="text-xs text-graphite">
                          {activeItem.retrieved_chunks.length} retrieved,{" "}
                          {activeItem.cited_chunk_ids.length} cited
                        </span>
                      </div>
                      <div className="grid gap-3">
                        {activeItem.retrieved_chunks.length ? (
                          activeItem.retrieved_chunks.map((chunk) => (
                            <div
                              className="rounded-md border border-line bg-surface p-3"
                              key={`${chunk.chunk_id}-${chunk.rank}`}
                            >
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="font-mono text-xs text-graphite">
                                  rank {chunk.rank} | {chunk.chunk_id}
                                </span>
                                <StatusBadge value={chunk.was_cited ? "cited" : "retrieved"} />
                              </div>
                              <p className="mt-1 text-xs font-semibold text-ink">
                                {chunk.document_title}
                              </p>
                              <p className="mt-2 text-sm leading-6 text-graphite">
                                {truncate(chunk.chunk_text, 620)}
                              </p>
                            </div>
                          ))
                        ) : (
                          <p className="text-sm text-graphite">
                            No retrieved chunks available for this response.
                          </p>
                        )}
                      </div>
                    </div>

                    <form
                      className="rounded-lg border border-line bg-white p-4 shadow-sm"
                      onSubmit={(event) => void saveReview(event)}
                    >
                      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <h2 className="text-sm font-semibold uppercase tracking-wide text-graphite">
                            Review form
                          </h2>
                          <p className="mt-1 text-sm text-graphite">
                            Scores are optional unless your local review protocol requires them.
                          </p>
                        </div>
                        <StatusBadge value={form.review_status} />
                      </div>

                      <div className="grid gap-3 md:grid-cols-3">
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Reviewer label</span>
                          <input
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                reviewer_label: event.target.value,
                              }))
                            }
                            value={form.reviewer_label}
                          />
                        </label>
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Reviewer type</span>
                          <select
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                reviewer_type: event.target.value as ReviewerType,
                              }))
                            }
                            value={form.reviewer_type}
                          >
                            <option value="self">self</option>
                            <option value="student">student</option>
                            <option value="domain_reviewer">domain_reviewer</option>
                            <option value="clinician">clinician</option>
                            <option value="unknown">unknown</option>
                          </select>
                        </label>
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Review status</span>
                          <select
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                review_status: event.target.value as ReviewStatus,
                              }))
                            }
                            value={form.review_status}
                          >
                            <option value="pending">pending</option>
                            <option value="completed">completed</option>
                            <option value="skipped">skipped</option>
                          </select>
                        </label>
                      </div>

                      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        {[
                          ["answer_correctness", "Answer correctness"],
                          ["groundedness", "Groundedness"],
                          ["citation_quality", "Citation quality"],
                          ["refusal_safety", "Refusal safety"],
                          ["confidence", "Confidence"],
                        ].map(([key, label]) => (
                          <label className="grid gap-1.5 text-sm" key={key}>
                            <span className="font-medium text-ink">{label}</span>
                            <select
                              className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                              onChange={(event) =>
                                setForm((current) => ({
                                  ...current,
                                  [key]: event.target.value,
                                }))
                              }
                              value={form[key as keyof ReviewFormState] as string}
                            >
                              {SCORE_OPTIONS.map((option) => (
                                <option key={option || "blank"} value={option}>
                                  {option || "n/a"}
                                </option>
                              ))}
                            </select>
                          </label>
                        ))}
                      </div>

                      <div className="mt-4 grid gap-3 md:grid-cols-3">
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Should refuse</span>
                          <select
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                should_refuse: event.target.value as TriState,
                              }))
                            }
                            value={form.should_refuse}
                          >
                            <option value="unknown">unknown</option>
                            <option value="yes">yes</option>
                            <option value="no">no</option>
                          </select>
                        </label>
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Did refuse</span>
                          <select
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                did_refuse: event.target.value as TriState,
                              }))
                            }
                            value={form.did_refuse}
                          >
                            <option value="unknown">unknown</option>
                            <option value="yes">yes</option>
                            <option value="no">no</option>
                          </select>
                        </label>
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Severity override</span>
                          <select
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                severity_override: event.target.value,
                              }))
                            }
                            value={form.severity_override}
                          >
                            <option value="">none</option>
                            <option value="low">low</option>
                            <option value="medium">medium</option>
                            <option value="high">high</option>
                            <option value="critical">critical</option>
                          </select>
                        </label>
                      </div>

                      <div className="mt-4">
                        <p className="mb-2 text-sm font-medium text-ink">
                          Reviewer failure categories
                        </p>
                        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                          {FAILURE_CATEGORIES.map((category) => (
                            <label
                              className="flex items-start gap-2 rounded-md border border-line bg-surface px-3 py-2 text-xs text-graphite"
                              key={category}
                            >
                              <input
                                checked={form.selected_failure_categories.includes(category)}
                                className="mt-0.5"
                                onChange={() => toggleCategory(category)}
                                type="checkbox"
                              />
                              <span>
                                <span className="font-semibold text-ink">
                                  {labelize(category)}
                                </span>
                                <span className="block font-mono text-[11px] text-graphite">
                                  {category}
                                </span>
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3 md:grid-cols-2">
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Adjudication</span>
                          <select
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                adjudication_status: event.target.value as ReviewFormState["adjudication_status"],
                              }))
                            }
                            value={form.adjudication_status}
                          >
                            <option value="none">none</option>
                            <option value="needs_second_review">needs_second_review</option>
                            <option value="adjudicated">adjudicated</option>
                          </select>
                        </label>
                        <label className="grid gap-1.5 text-sm">
                          <span className="font-medium text-ink">Reviewer time seconds</span>
                          <input
                            className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                            min="0"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                reviewer_time_seconds: event.target.value,
                              }))
                            }
                            type="number"
                            value={form.reviewer_time_seconds}
                          />
                        </label>
                      </div>

                      <label className="mt-4 grid gap-1.5 text-sm">
                        <span className="font-medium text-ink">Notes</span>
                        <textarea
                          className="min-h-28 rounded-md border border-line bg-white px-3 py-2 text-sm leading-6 text-ink"
                          onChange={(event) =>
                            setForm((current) => ({
                              ...current,
                              review_notes: event.target.value,
                            }))
                          }
                          value={form.review_notes}
                        />
                      </label>

                      <label className="mt-3 flex items-center gap-2 text-xs text-graphite">
                        <input
                          checked={form.sample}
                          onChange={(event) =>
                            setForm((current) => ({
                              ...current,
                              sample: event.target.checked,
                            }))
                          }
                          type="checkbox"
                        />
                        Mark as sample fixture or workflow test
                      </label>

                      {saveError ? (
                        <div className="mt-4 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                          {saveError}
                        </div>
                      ) : null}
                      {saveMessage ? (
                        <div className="mt-4 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
                          {saveMessage}
                        </div>
                      ) : null}

                      <div className="mt-4 flex flex-wrap gap-2">
                        <button
                          className="rounded-md bg-clinical px-4 py-2 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
                          disabled={saving}
                          type="submit"
                        >
                          {saving ? "Saving..." : "Save review"}
                        </button>
                        <button
                          className="rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-white"
                          onClick={() => setForm(formFromReview(activeItem.manual_review))}
                          type="button"
                        >
                          Reset form
                        </button>
                      </div>
                    </form>
                  </>
                )}
              </section>
            </div>
          </>
        ) : !experimentId && !queue.loading ? (
          <EmptyState
            title="Choose an experiment"
            message="Select an experiment to load its human review queue and calibration summary."
            showSeedCommands={false}
          />
        ) : null}
      </div>
    </>
  );
}
