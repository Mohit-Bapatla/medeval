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
    return <EmptyState title="Trace not found" message="The backend did not return this response trace." />;
  }

  const evaluation = trace.data.evaluation;
  const claimSupport = evaluation?.metadata.claim_support as ClaimSupportMetadata | undefined;
  const failureAnalysis = evaluation?.metadata.failure_analysis as FailureAnalysisMetadata | undefined;

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
      setReviewError(caught instanceof Error ? caught.message : "Unable to save review");
    }
  }

  return (
    <>
      <PageHeader
        title="Response Trace"
        description="Question, gold answer, model answer, retrieved chunks, citations, scores, and failure analysis."
      />
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-graphite">Question</p>
          <h2 className="mt-2 text-lg font-semibold">{trace.data.qa_example.question}</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <StatusBadge value={`gold: ${trace.data.qa_example.answerability}`} />
            <StatusBadge value={`model: ${trace.data.model_response.answerability}`} />
          </div>
          <p className="mt-5 text-sm font-semibold">Gold answer</p>
          <p className="mt-2 text-sm leading-6 text-graphite">{trace.data.qa_example.gold_answer}</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase text-graphite">Model answer</p>
          <p className="mt-2 text-sm leading-6 text-graphite">{trace.data.model_response.answer_text}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <MetricCard label="Confidence" value={formatMetric(trace.data.model_response.confidence)} />
            <MetricCard label="Latency" value={`${trace.data.model_response.latency_ms ?? "n/a"} ms`} />
          </div>
        </div>
      </section>
      <section className="mt-5 grid gap-4 md:grid-cols-4">
        <MetricCard label="Correctness" value={formatMetric(evaluation?.correctness_score)} />
        <MetricCard label="Groundedness" value={formatMetric(evaluation?.groundedness_score)} />
        <MetricCard label="Citation recall" value={formatMetric(evaluation?.citation_recall)} />
        <MetricCard label="Retrieval recall" value={formatMetric(evaluation?.retrieval_recall)} />
        <MetricCard label="Overall" value={formatMetric(evaluation?.overall_score)} />
        <MetricCard label="Refusal" value={formatMetric(evaluation?.refusal_score)} />
        <MetricCard label="Input tokens" value={trace.data.model_response.input_tokens ?? "n/a"} />
        <MetricCard label="Cost" value={trace.data.model_response.estimated_cost ?? "n/a"} />
      </section>
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Evaluation outcome</h2>
          <div className="flex flex-wrap gap-2">
            <StatusBadge value={evaluation?.failure_type || "none"} />
            <StatusBadge value={evaluation?.hallucination_flag ? "hallucination" : "no hallucination flag"} />
          </div>
        </div>
        <p className="mt-3 text-sm leading-6 text-graphite">
          {failureAnalysis?.failure_reason ||
            evaluation?.judge_explanation ||
            "No evaluation explanation available."}
        </p>
        {failureAnalysis ? (
          <div className="mt-4 grid gap-3 text-sm text-graphite md:grid-cols-3">
            <p>Evidence: {failureAnalysis.evidence_summary ?? "n/a"}</p>
            <p>Retrieval failure: {failureAnalysis.retrieval_failure ? "yes" : "no"}</p>
            <p>Generation failure: {failureAnalysis.generation_failure ? "yes" : "no"}</p>
          </div>
        ) : null}
      </section>
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Claim support heuristic</h2>
            <p className="mt-1 text-sm text-graphite">
              Deterministic token-overlap check against cited retrieved chunks; not benchmark-grade.
            </p>
          </div>
          <StatusBadge value={claimSupport?.method || "not available"} />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <MetricCard label="Claims" value={claimSupport?.claim_count ?? "n/a"} />
          <MetricCard label="Support rate" value={formatMetric(claimSupport?.claim_support_rate)} />
          <MetricCard label="Citation coverage" value={formatMetric(claimSupport?.citation_coverage)} />
          <MetricCard label="Unsupported" value={formatMetric(claimSupport?.unsupported_claim_rate)} />
        </div>
        {claimSupport?.claims?.length ? (
          <div className="mt-4 grid gap-3">
            {claimSupport.claims.map((claim) => (
              <article className="rounded-md border border-line bg-surface p-3" key={claim.claim_index}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium">Claim {claim.claim_index + 1}</p>
                  <StatusBadge value={claim.support_status} />
                </div>
                <p className="mt-2 text-sm leading-6 text-graphite">{claim.claim_text}</p>
                <p className="mt-2 text-xs text-graphite">
                  Token overlap {claim.token_overlap === null || claim.token_overlap === undefined ? "n/a" : claim.token_overlap.toFixed(3)}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-graphite">No claim-level support details available.</p>
        )}
      </section>
      <section className="mt-5">
        <h2 className="mb-3 text-lg font-semibold">Retrieved chunks</h2>
        <div className="grid gap-3">
          {trace.data.retrieved_chunks.map((chunk) => (
            <article
              className={`rounded-lg border p-4 shadow-sm ${
                chunk.was_cited ? "border-clinical bg-clinical/5" : "border-line bg-white"
              }`}
              key={chunk.chunk_id}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="font-semibold">
                  Rank {chunk.rank} - {chunk.document_title} - chunk {chunk.chunk_index}
                </p>
                <StatusBadge value={chunk.was_cited ? "cited" : "retrieved"} />
              </div>
              <p className="mt-2 text-xs text-graphite">
                Similarity {chunk.similarity_score.toFixed(3)}
              </p>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-graphite">
                {chunk.chunk_text}
              </p>
            </article>
          ))}
        </div>
      </section>
      <details className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <summary className="cursor-pointer font-semibold">Raw provider output</summary>
        <pre className="mt-4 overflow-x-auto rounded-md bg-surface p-4 text-xs text-graphite">
          {JSON.stringify(trace.data.model_response.raw_model_output, null, 2)}
        </pre>
      </details>
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Human review</h2>
        <p className="mt-1 text-sm text-graphite">
          Optional local review labels. No fake reviews are seeded.
        </p>
        {trace.data.human_reviews.length ? (
          <div className="mt-4 grid gap-3">
            {trace.data.human_reviews.map((review) => (
              <article className="rounded-md border border-line bg-surface p-3" key={review.id}>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge value={review.correctness_label || "correctness unset"} />
                  <StatusBadge value={review.groundedness_label || "groundedness unset"} />
                  <StatusBadge value={review.refusal_label || "refusal unset"} />
                </div>
                <p className="mt-2 text-sm text-graphite">
                  {review.reviewer_name || "Unnamed reviewer"}
                  {review.reviewer_role ? ` - ${review.reviewer_role}` : ""}
                </p>
                {review.notes ? <p className="mt-2 text-sm leading-6 text-graphite">{review.notes}</p> : null}
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-graphite">No human reviews yet.</p>
        )}
        <form className="mt-5 grid gap-3 md:grid-cols-2" onSubmit={(event) => void submitHumanReview(event)}>
          <input className="rounded-md border border-line px-3 py-2 text-sm" name="reviewer_name" placeholder="Reviewer name" />
          <input className="rounded-md border border-line px-3 py-2 text-sm" name="reviewer_role" placeholder="Reviewer role" />
          <select className="rounded-md border border-line px-3 py-2 text-sm" name="correctness_label" defaultValue="">
            <option value="">Correctness label</option>
            <option value="correct">Correct</option>
            <option value="partially_correct">Partially correct</option>
            <option value="incorrect">Incorrect</option>
            <option value="unsure">Unsure</option>
          </select>
          <select className="rounded-md border border-line px-3 py-2 text-sm" name="groundedness_label" defaultValue="">
            <option value="">Groundedness label</option>
            <option value="grounded">Grounded</option>
            <option value="partially_grounded">Partially grounded</option>
            <option value="unsupported">Unsupported</option>
            <option value="unsure">Unsure</option>
          </select>
          <select className="rounded-md border border-line px-3 py-2 text-sm" name="refusal_label" defaultValue="">
            <option value="">Refusal label</option>
            <option value="correct_refusal">Correct refusal</option>
            <option value="failed_refusal">Failed refusal</option>
            <option value="over_refusal">Over refusal</option>
            <option value="not_applicable">Not applicable</option>
          </select>
          <textarea className="min-h-24 rounded-md border border-line px-3 py-2 text-sm md:col-span-2" name="notes" placeholder="Review notes" />
          <div className="flex items-center gap-3 md:col-span-2">
            <button className="rounded-md bg-clinical px-3 py-2 text-sm font-medium text-white" type="submit">
              Save review
            </button>
            {reviewMessage ? <span className="text-sm text-clinical">{reviewMessage}</span> : null}
            {reviewError ? <span className="text-sm text-signal">{reviewError}</span> : null}
          </div>
        </form>
      </section>
    </>
  );
}
