"use client";

import { useParams } from "next/navigation";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatMetric } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { ResponseTrace } from "@/types/traces";

export default function TracePage() {
  const params = useParams<{ responseId: string }>();
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
          {evaluation?.judge_explanation || "No evaluation explanation available."}
        </p>
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
    </>
  );
}
