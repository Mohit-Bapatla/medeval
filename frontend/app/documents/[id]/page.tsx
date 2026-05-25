"use client";

import { useParams } from "next/navigation";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate, truncate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { DocumentChunk, DocumentDetail } from "@/types/documents";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const document = useApi<DocumentDetail>(params.id ? `/documents/${params.id}` : null);
  const chunks = useApi<DocumentChunk[]>(params.id ? `/documents/${params.id}/chunks` : null);

  if (document.loading || chunks.loading) {
    return <LoadingState label="Loading document..." />;
  }
  if (document.error) {
    return <ErrorState message={document.error} />;
  }
  if (!document.data) {
    return <EmptyState title="Document not found" message="The backend did not return this document." />;
  }

  return (
    <>
      <PageHeader
        title={document.data.title}
        description="Document detail, cleaned text preview, and chunk-level retrieval evidence."
      />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Source" value={document.data.source_type} />
        <MetricCard label="Document type" value={document.data.document_type} />
        <MetricCard label="Chunks" value={chunks.data?.length ?? 0} />
        <MetricCard label="Created" value={formatDate(document.data.created_at)} />
      </div>
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap gap-2">
          <StatusBadge value={document.data.source_type} />
          <StatusBadge value={document.data.document_type} />
        </div>
        <h2 className="mt-4 text-lg font-semibold">Cleaned text preview</h2>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-graphite">
          {truncate(document.data.cleaned_text, 1200)}
        </p>
      </section>
      <section className="mt-5">
        <h2 className="mb-3 text-lg font-semibold">Chunks</h2>
        {chunks.error ? <ErrorState message={chunks.error} /> : null}
        {chunks.data?.length === 0 ? (
          <EmptyState title="No chunks found" message="Chunk this document from the API or seed script." />
        ) : null}
        <div className="grid gap-3">
          {chunks.data?.map((chunk) => (
            <article className="rounded-lg border border-line bg-white p-4 shadow-sm" key={chunk.id}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold">Chunk {chunk.chunk_index}</p>
                <StatusBadge value={chunk.embedding_model ? "embedded" : "not embedded"} />
              </div>
              <p className="mt-2 text-xs text-graphite">Approx tokens: {chunk.token_count}</p>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-graphite">
                {chunk.chunk_text}
              </p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
