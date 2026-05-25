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
    return (
      <EmptyState
        title="Document not found"
        message="The backend did not return this document."
        showSeedCommands={false}
      />
    );
  }

  return (
    <>
      <PageHeader
        title={document.data.title}
        description="Document detail, cleaned text preview, and chunk-level retrieval evidence used in RAG evaluation."
      />

      {/* Metric summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          label="Source type"
          value={document.data.source_type}
          accent="info"
        />
        <MetricCard
          label="Document type"
          value={document.data.document_type}
          accent="info"
        />
        <MetricCard
          label="Chunks"
          value={chunks.data?.length ?? "—"}
        />
        <MetricCard
          label="Created"
          value={formatDate(document.data.created_at)}
        />
      </div>

      {/* Cleaned text */}
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-ink">
            Cleaned text preview
          </h2>
          <div className="flex flex-wrap gap-2">
            <StatusBadge value={document.data.source_type} />
            <StatusBadge value={document.data.document_type} />
          </div>
        </div>
        <div className="mt-4 rounded-md bg-surface p-4">
          <p className="whitespace-pre-wrap text-sm leading-7 text-graphite">
            {truncate(document.data.cleaned_text, 1400)}
          </p>
        </div>
      </section>

      {/* Chunks */}
      <section className="mt-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">
            Chunks
            {chunks.data?.length ? (
              <span className="ml-2 rounded-full bg-surface px-2 py-0.5 text-xs font-medium text-graphite border border-line">
                {chunks.data.length}
              </span>
            ) : null}
          </h2>
          <p className="text-xs text-graphite">
            Indexed for vector retrieval
          </p>
        </div>
        {chunks.error ? <ErrorState message={chunks.error} /> : null}
        {chunks.data?.length === 0 ? (
          <EmptyState
            title="No chunks found"
            message="Chunk this document from the API or seed script."
          />
        ) : null}
        <div className="grid gap-3">
          {chunks.data?.map((chunk) => (
            <article
              className="rounded-lg border border-line bg-white p-4 shadow-sm"
              key={chunk.id}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-surface px-2 py-0.5 text-xs font-semibold text-graphite border border-line">
                    #{chunk.chunk_index}
                  </span>
                  <p className="text-sm font-semibold text-ink">
                    Chunk {chunk.chunk_index}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-graphite">
                    ~{chunk.token_count} tokens
                  </span>
                  <StatusBadge
                    value={chunk.embedding_model ? "embedded" : "not embedded"}
                  />
                </div>
              </div>
              <div className="mt-3 rounded-md bg-surface p-3">
                <p className="whitespace-pre-wrap text-sm leading-7 text-graphite">
                  {chunk.chunk_text}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
