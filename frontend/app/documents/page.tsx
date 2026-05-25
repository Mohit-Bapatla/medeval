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
        description="Source documents and cleaned text that feed chunking, embeddings, retrieval, and evidence-grounded evaluation."
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
        <div className="overflow-hidden rounded-lg border border-line bg-white shadow-sm">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-surface text-xs uppercase text-graphite">
              <tr>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Organization</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {data.map((document) => (
                <tr className="border-t border-line" key={document.id}>
                  <td className="px-4 py-3 font-medium">
                    <Link className="text-clinical hover:underline" href={`/documents/${document.id}`}>
                      {document.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3"><StatusBadge value={document.source_type} /></td>
                  <td className="px-4 py-3">{document.document_type}</td>
                  <td className="px-4 py-3">{document.organization_name || "n/a"}</td>
                  <td className="px-4 py-3">{formatDate(document.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}
