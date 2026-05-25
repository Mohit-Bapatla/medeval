"use client";

import Link from "next/link";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { DocumentItem } from "@/types/documents";

export default function DocumentsPage() {
  const { data, error, loading } = useApi<DocumentItem[]>("/documents");

  return (
    <>
      <PageHeader
        title="Documents"
        description="Source documents processed into clean text, chunks, and embeddings for retrieval-augmented evaluation. Each document feeds the chunking pipeline and vector index."
      />
      {loading ? <LoadingState label="Loading documents..." /> : null}
      {error ? <ErrorState message={error} /> : null}
      {data?.length === 0 ? (
        <EmptyState
          title="No documents found"
          message="Seed synthetic sample documents to inspect chunks and retrieval evidence."
        />
      ) : null}
      {data?.length ? (
        <div className="overflow-x-auto rounded-lg border border-line bg-white shadow-sm">
          <table className="w-full min-w-[640px] border-collapse text-left text-sm">
            <thead className="border-b border-line bg-surface">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Title
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Source type
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Document type
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Organization
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-graphite">
                  Created
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.map((document) => (
                <tr
                  className="transition-colors hover:bg-surface/60"
                  key={document.id}
                >
                  <td className="px-4 py-3.5">
                    <Link
                      className="font-semibold text-clinical hover:underline"
                      href={`/documents/${document.id}`}
                    >
                      {document.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge value={document.source_type} />
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge value={document.document_type} />
                  </td>
                  <td className="px-4 py-3.5 text-graphite">
                    {document.organization_name || (
                      <span className="text-line">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-graphite">
                    {formatDate(document.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-line px-4 py-2.5">
            <p className="text-xs text-graphite">
              {data.length} document{data.length !== 1 ? "s" : ""} · Synthetic
              sample data
            </p>
          </div>
        </div>
      ) : null}
    </>
  );
}
