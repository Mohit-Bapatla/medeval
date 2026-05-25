"use client";

import { useParams } from "next/navigation";
import { FormEvent, useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiFetch } from "@/lib/api";
import { formatMetric } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type {
  ClaimSupportMetadata,
  FailureAnalysisMetadata,
  ResponseTrace,
} from "@/types/traces";

function ScoreBar({ value }: { value: number | null | undefined }) {
  if (value == null) return <span className="text-graphite">—</span>;
  const pct = Math.round(value * 100);
  const color =
    pct >= 75 ? "bg-success" : pct >= 50 ? "bg-signal" : "bg-danger";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-line">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="tabular-nums text-sm font-semibold text-ink">{pct}%</span>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-graphite">
      {children}
    </p>
  );
}

export default function TracePage() {
  const params = useParams<{ responseId: string }>();
  const [reviewMessage, setReviewMessage] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const trace = useApi<ResponseTrace>(
    params.responseId ? `/responses/${params.responseId}/trace` : null,
  );

  if (trace.loading) {
    return <LoadingState label="Loading trace..." />;
  }
  if (trace.error) {
    return <ErrorState message={trace.error} />;
  }
  if (!trace.data) {
    return (
      <EmptyState
        title="Trace not found"
        message="The backend did not return this response trace."
        showSeedCommands={false}
      />
    );
  }

  const evaluation = trace.data.evaluation;
  const claimSupport = evaluation?.metadata.claim_support as
    | ClaimSupportMetadata
    | undefined;
  const failureAnalysis = evaluation?.metadata.failure_analysis as
    | FailureAnalysisMetadata
    | undefined;
  const hasHallucination = evaluation?.hallucination_flag === true;
  const failureType = evaluation?.failure_type;

  async function submitHumanReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!params.responseId) {
      return;
    }
    const formData = new FormData(event.currentTarget);
    setReviewMessage(null);
    setReviewError(null);
    try {
      await apiFetch(`/responses/${params.responseId}/human-review`, {
        method: "POST",
        body: JSON.stringify({
          reviewer_name: formData.get("reviewer_name") || null,
          reviewer_role: formData.get("reviewer_role") || null,
          correctness_label: formData.get("correctness_label") || null,
          groundedness_label: formData.get("groundedness_label") || null,
          refusal_label: formData.get("refusal_label") || null,
          notes: formData.get("notes") || null,
          metadata: { source: "frontend_trace_viewer" },
        }),
      });
      event.currentTarget.reset();
      setReviewMessage("Human review saved.");
      trace.reload();
    } catch (caught) {
      setReviewError(
        caught instanceof Error ? caught.message : "Unable to save review",
      );
    }
  }

  return (
    <>
      <PageHeader
        title="Response Trace"
        description="Full evaluation trace — question, gold answer, model answer, retrieved evidence, citation analysis, and failure classification."
      />

      {/* Hallucination alert banner */}
      {hasHallucination ? (
        <div className="mb-5 flex items-start gap-3 rounded-lg border border-danger/40 bg-danger/10 px-4 py-3">
          <span className="mt-0.5 text-danger text-lg" aria-hidden="true">⚑</span>
          <div>
            <p className="text-sm font-bold text-danger">Hallucination flagged</p>
            <p className="text-xs text-graphite mt-0.5">
              The evaluator detected content not supported by retrieved evidence.
            </p>
          </div>
          {failureType ? (
            <div className="ml-auto shrink-0">
              <StatusBadge value={failureType} />
            </div>
          ) : null}
        </div>
      ) : null}

      {/* Q&A comparison */}
      <section className="grid gap-4 lg:grid-cols-2">
        {/* Question + Gold answer */}
        <div className="rounded-lg border border-success/30 bg-white shadow-sm">
          <div className="border-b border-success/20 bg-success/5 px-5 py-3">
            <SectionLabel>Question &amp; Gold Answer</SectionLabel>
          </div>
          <div className="p-5">
            <h2 className="text-base font-bold text-ink leading-6">
              {trace.data.qa_example.question}
            </h2>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs text-graphite">
                Gold answerability:
              </span>
              <StatusBadge
                value={trace.data.qa_example.answerability}
              />
            </div>
            <div className="mt-4 border-t border-line pt-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-success">
                Gold answer
              </p>
              <p className="mt-2 text-sm leading-7 text-graphite">
                {trace.data.qa_example.gold_answer}
              </p>
            </div>
          </div>
        </div>

        {/* Model answer */}
        <div
          className={`rounded-lg border bg-white shadow-sm ${
            hasHallucination
              ? "border-danger/30"
              : "border-clinical/30"
          }`}
        >
          <div
            className={`border-b px-5 py-3 ${
              hasHallucination
                ? "border-danger/20 bg-danger/5"
                : "border-clinical/20 bg-clinical/5"
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <SectionLabel>Model Answer</SectionLabel>
              <div className="flex gap-2">
                <StatusBadge
                  value={`model: ${trace.data.model_response.answerability}`}
                />
                {hasHallucination ? (
                  <StatusBadge value="hallucination" />
                ) : null}
              </div>
            </div>
          </div>
          <div className="p-5">
            <p className="text-sm leading-7 text-graphite">
              {trace.data.model_response.answer_text}
            </p>
            <div className="mt-4 grid grid-cols-2 gap-3 border-t border-line pt-4">
              <MetricCard
                label="Confidence"
                value={formatMetric(trace.data.model_response.confidence)}
              />
              <MetricCard
                label="Latency"
                value={
                  trace.data.model_response.latency_ms != null
                    ? `${trace.data.model_response.latency_ms} ms`
                    : "n/a"
                }
              />
            </div>
          </div>
        </div>
      </section>

      {/* Evaluation scores */}
      <section className="mt-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-graphite">
            Evaluation scores
          </h2>
          <p className="text-xs text-graphite">
            Deterministic MVP evaluator — not LLM-judge scores
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Correctness"
            value={formatMetric(evaluation?.correctness_score)}
            accent={
              evaluation?.correctness_score != null
                ? evaluation.correctness_score >= 0.75
                  ? "success"
                  : evaluation.correctness_score >= 0.5
                    ? "warning"
                    : "danger"
                : undefined
            }
          />
          <MetricCard
            label="Groundedness"
            value={formatMetric(evaluation?.groundedness_score)}
            accent={
              evaluation?.groundedness_score != null
                ? evaluation.groundedness_score >= 0.75
                  ? "success"
                  : evaluation.groundedness_score >= 0.5
                    ? "warning"
                    : "danger"
                : undefined
            }
          />
          <MetricCard
            label="Citation recall"
            value={formatMetric(evaluation?.citation_recall)}
          />
          <MetricCard
            label="Retrieval recall"
            value={formatMetric(evaluation?.retrieval_recall)}
          />
          <MetricCard
            label="Overall score"
            value={formatMetric(evaluation?.overall_score)}
            accent={
              evaluation?.overall_score != null
                ? evaluation.overall_score >= 0.75
                  ? "success"
                  : evaluation.overall_score >= 0.5
                    ? "warning"
                    : "danger"
                : undefined
            }
          />
          <MetricCard
            label="Refusal score"
            value={formatMetric(evaluation?.refusal_score)}
          />
          <MetricCard
            label="Input tokens"
            value={trace.data.model_response.input_tokens ?? "n/a"}
          />
          <MetricCard
            label="Est. cost"
            value={trace.data.model_response.estimated_cost ?? "n/a"}
          />
        </div>

        {/* Score bars */}
        <div className="mt-4 rounded-lg border border-line bg-white p-5 shadow-sm">
          <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-graphite">
            Score visualization
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              ["Correctness", evaluation?.correctness_score],
              ["Groundedness", evaluation?.groundedness_score],
              ["Citation recall", evaluation?.citation_recall],
              ["Retrieval recall", evaluation?.retrieval_recall],
              ["Overall", evaluation?.overall_score],
              ["Refusal", evaluation?.refusal_score],
            ].map(([label, val]) => (
              <div key={String(label)} className="flex items-center justify-between gap-3">
                <span className="text-xs text-graphite w-28 shrink-0">{label}</span>
                <ScoreBar value={val as number | null} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Failure analysis */}
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h2 className="text-base font-semibold text-ink">
            Evaluation outcome
          </h2>
          <div className="flex flex-wrap gap-2">
            <StatusBadge value={evaluation?.failure_type || "none"} />
            {hasHallucination ? (
              <StatusBadge value="hallucination" />
            ) : (
              <StatusBadge value="no hallucination flag" />
            )}
          </div>
        </div>
        <p className="mt-3 text-sm leading-7 text-graphite">
          {failureAnalysis?.failure_reason ||
            evaluation?.judge_explanation ||
            "No evaluation explanation available."}
        </p>
        {failureAnalysis ? (
          <div className="mt-4 grid gap-2 rounded-md bg-surface p-4 text-sm sm:grid-cols-3">
            <div>
              <p className="text-xs font-semibold text-graphite">Evidence summary</p>
              <p className="mt-1 text-ink">
                {failureAnalysis.evidence_summary ?? "n/a"}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-graphite">Retrieval failure</p>
              <p className="mt-1">
                {failureAnalysis.retrieval_failure ? (
                  <span className="text-danger font-semibold">Yes</span>
                ) : (
                  <span className="text-success font-semibold">No</span>
                )}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-graphite">Generation failure</p>
              <p className="mt-1">
                {failureAnalysis.generation_failure ? (
                  <span className="text-danger font-semibold">Yes</span>
                ) : (
                  <span className="text-success font-semibold">No</span>
                )}
              </p>
            </div>
          </div>
        ) : null}
      </section>

      {/* Claim support */}
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-ink">
              Claim-level citation support
            </h2>
            <p className="mt-1 text-xs leading-5 text-graphite">
              Deterministic token-overlap heuristic against cited retrieved
              chunks. Not a benchmark-grade citation verifier.
            </p>
          </div>
          <StatusBadge value={claimSupport?.method || "not available"} />
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Claims detected"
            value={claimSupport?.claim_count ?? "n/a"}
          />
          <MetricCard
            label="Support rate"
            value={formatMetric(claimSupport?.claim_support_rate)}
            accent={
              claimSupport?.claim_support_rate != null
                ? claimSupport.claim_support_rate >= 0.75
                  ? "success"
                  : claimSupport.claim_support_rate >= 0.5
                    ? "warning"
                    : "danger"
                : undefined
            }
          />
          <MetricCard
            label="Citation coverage"
            value={formatMetric(claimSupport?.citation_coverage)}
          />
          <MetricCard
            label="Unsupported rate"
            value={formatMetric(claimSupport?.unsupported_claim_rate)}
            accent={
              claimSupport?.unsupported_claim_rate != null
                ? claimSupport.unsupported_claim_rate > 0.5
                  ? "danger"
                  : claimSupport.unsupported_claim_rate > 0.2
                    ? "warning"
                    : "success"
                : undefined
            }
          />
        </div>
        {claimSupport?.claims?.length ? (
          <div className="mt-4 grid gap-2">
            {claimSupport.claims.map((claim) => {
              const isSupported =
                claim.support_status === "supported" ||
                claim.support_status?.includes("supported");
              return (
                <article
                  className={`rounded-md border p-3 ${
                    isSupported
                      ? "border-success/30 bg-success/5"
                      : "border-danger/30 bg-danger/5"
                  }`}
                  key={claim.claim_index}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs font-semibold text-graphite">
                      Claim {claim.claim_index + 1}
                    </p>
                    <div className="flex items-center gap-2">
                      {claim.token_overlap != null ? (
                        <span className="text-xs text-graphite">
                          overlap: {claim.token_overlap.toFixed(3)}
                        </span>
                      ) : null}
                      <StatusBadge value={claim.support_status} />
                    </div>
                  </div>
                  <p className="mt-1.5 text-sm leading-6 text-ink">
                    {claim.claim_text}
                  </p>
                </article>
              );
            })}
          </div>
        ) : (
          <p className="mt-4 text-sm text-graphite">
            No claim-level support details available.
          </p>
        )}
      </section>

      {/* Retrieved chunks */}
      <section className="mt-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">
            Retrieved chunks
            <span className="ml-2 rounded-full border border-line bg-surface px-2 py-0.5 text-xs font-medium text-graphite">
              {trace.data.retrieved_chunks.length}
            </span>
          </h2>
          <div className="flex gap-3 text-xs text-graphite">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-success/60" />
              Cited
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-line" />
              Retrieved only
            </span>
          </div>
        </div>
        <div className="grid gap-3">
          {trace.data.retrieved_chunks.map((chunk) => (
            <article
              className={`rounded-lg border p-4 shadow-sm ${
                chunk.was_cited
                  ? "border-success/30 bg-success/5"
                  : "border-line bg-white"
              }`}
              key={chunk.chunk_id}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-1.5 py-0.5 text-xs font-bold ${
                        chunk.was_cited
                          ? "bg-success/10 text-success"
                          : "bg-surface text-graphite border border-line"
                      }`}
                    >
                      Rank {chunk.rank}
                    </span>
                    <p className="text-sm font-semibold text-ink">
                      {chunk.document_title}
                    </p>
                    <span className="text-xs text-graphite">
                      chunk #{chunk.chunk_index}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-graphite">
                    sim: {chunk.similarity_score.toFixed(3)}
                  </span>
                  <StatusBadge value={chunk.was_cited ? "cited" : "retrieved"} />
                </div>
              </div>
              <div className="mt-3 rounded-md bg-white/70 p-3 border border-white">
                <p className="whitespace-pre-wrap text-sm leading-7 text-graphite">
                  {chunk.chunk_text}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Raw output */}
      <details className="mt-5 rounded-lg border border-line bg-white shadow-sm">
        <summary className="cursor-pointer select-none px-5 py-4 text-sm font-semibold text-ink hover:text-clinical">
          Raw provider output
          <span className="ml-2 text-xs font-normal text-graphite">
            (click to expand)
          </span>
        </summary>
        <div className="border-t border-line px-5 pb-5 pt-4">
          <pre className="overflow-x-auto rounded-md bg-surface p-4 text-xs leading-5 text-graphite">
            {JSON.stringify(
              trace.data.model_response.raw_model_output,
              null,
              2,
            )}
          </pre>
        </div>
      </details>

      {/* Human review */}
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-ink">Human review</h2>
        <p className="mt-1 text-xs leading-5 text-graphite">
          Optional local review labels for correctness, groundedness, and
          refusal quality. No fake reviews are seeded.
        </p>

        {trace.data.human_reviews.length ? (
          <div className="mt-4 grid gap-3">
            {trace.data.human_reviews.map((review) => (
              <article
                className="rounded-md border border-line bg-surface p-3"
                key={review.id}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-ink">
                    {review.reviewer_name || "Unnamed reviewer"}
                    {review.reviewer_role ? (
                      <span className="ml-1.5 text-xs font-normal text-graphite">
                        — {review.reviewer_role}
                      </span>
                    ) : null}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    <StatusBadge
                      value={review.correctness_label || "correctness unset"}
                    />
                    <StatusBadge
                      value={review.groundedness_label || "groundedness unset"}
                    />
                    <StatusBadge
                      value={review.refusal_label || "refusal unset"}
                    />
                  </div>
                </div>
                {review.notes ? (
                  <p className="mt-2 text-sm leading-6 text-graphite">
                    {review.notes}
                  </p>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-graphite">No human reviews yet.</p>
        )}

        {/* Review form */}
        <div className="mt-5 border-t border-line pt-5">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-graphite">
            Add review
          </p>
          <form
            className="grid gap-3 md:grid-cols-2"
            onSubmit={(event) => void submitHumanReview(event)}
          >
            <input
              className="rounded-md border border-line px-3 py-2 text-sm focus:border-clinical focus:outline-none"
              name="reviewer_name"
              placeholder="Reviewer name"
            />
            <input
              className="rounded-md border border-line px-3 py-2 text-sm focus:border-clinical focus:outline-none"
              name="reviewer_role"
              placeholder="Reviewer role"
            />
            <select
              className="rounded-md border border-line px-3 py-2 text-sm focus:border-clinical focus:outline-none"
              name="correctness_label"
              defaultValue=""
            >
              <option value="">Correctness label</option>
              <option value="correct">Correct</option>
              <option value="partially_correct">Partially correct</option>
              <option value="incorrect">Incorrect</option>
              <option value="unsure">Unsure</option>
            </select>
            <select
              className="rounded-md border border-line px-3 py-2 text-sm focus:border-clinical focus:outline-none"
              name="groundedness_label"
              defaultValue=""
            >
              <option value="">Groundedness label</option>
              <option value="grounded">Grounded</option>
              <option value="partially_grounded">Partially grounded</option>
              <option value="unsupported">Unsupported</option>
              <option value="unsure">Unsure</option>
            </select>
            <select
              className="rounded-md border border-line px-3 py-2 text-sm focus:border-clinical focus:outline-none"
              name="refusal_label"
              defaultValue=""
            >
              <option value="">Refusal label</option>
              <option value="correct_refusal">Correct refusal</option>
              <option value="failed_refusal">Failed refusal</option>
              <option value="over_refusal">Over refusal</option>
              <option value="not_applicable">Not applicable</option>
            </select>
            <div className="md:col-span-2">
              <textarea
                className="w-full min-h-20 rounded-md border border-line px-3 py-2 text-sm focus:border-clinical focus:outline-none"
                name="notes"
                placeholder="Review notes (optional)"
              />
            </div>
            <div className="flex items-center gap-3 md:col-span-2">
              <button
                className="rounded-md bg-clinical px-4 py-2 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-90"
                type="submit"
              >
                Save review
              </button>
              {reviewMessage ? (
                <span className="text-sm text-success">{reviewMessage}</span>
              ) : null}
              {reviewError ? (
                <span className="text-sm text-danger">{reviewError}</span>
              ) : null}
            </div>
          </form>
        </div>
      </section>
    </>
  );
}
