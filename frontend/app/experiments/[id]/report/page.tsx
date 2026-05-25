"use client";

import { useParams } from "next/navigation";
import { useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { formatDate, formatMetric } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { ExperimentReport } from "@/types/experiments";

export default function ExperimentReportPage() {
  const params = useParams<{ id: string }>();
  const report = useApi<ExperimentReport>(params.id ? `/experiments/${params.id}/report` : null);
  const [message, setMessage] = useState<string | null>(null);

  function downloadMarkdown() {
    if (!report.data) {
      return;
    }
    const blob = new Blob([report.data.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${report.data.experiment.name.replaceAll(" ", "_")}_report.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function copyMarkdown() {
    if (!report.data) {
      return;
    }
    await navigator.clipboard.writeText(report.data.markdown);
    setMessage("Markdown copied.");
  }

  if (report.loading) {
    return <LoadingState label="Loading report..." />;
  }
  if (report.error) {
    return <ErrorState message={report.error} />;
  }
  if (!report.data) {
    return <EmptyState title="Report not found" message="The backend did not return this report." />;
  }

  return (
    <>
      <PageHeader
        title={`Report: ${report.data.experiment.name}`}
        description="Computed local report preview. This is not a validated benchmark report."
        action={
          <div className="flex gap-2">
            <button className="rounded-md border border-line px-3 py-2 text-sm" onClick={() => void copyMarkdown()} type="button">
              Copy Markdown
            </button>
            <button className="rounded-md bg-clinical px-3 py-2 text-sm font-medium text-white" onClick={downloadMarkdown} type="button">
              Download .md
            </button>
          </div>
        }
      />
      {message ? <p className="mb-4 text-sm text-clinical">{message}</p> : null}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Examples" value={report.data.results.example_count} />
        <MetricCard label="Correctness" value={formatMetric(report.data.results.avg_correctness)} />
        <MetricCard label="Groundedness" value={formatMetric(report.data.results.avg_groundedness)} />
        <MetricCard label="Hallucination" value={formatMetric(report.data.results.hallucination_rate)} />
      </div>
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Report metadata</h2>
        <p className="mt-2 text-sm text-graphite">Generated {formatDate(report.data.generated_at)}</p>
        <p className="mt-3 text-sm leading-6 text-signal">{report.data.disclaimer}</p>
      </section>
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Markdown preview</h2>
        <pre className="mt-4 max-h-[720px] overflow-auto whitespace-pre-wrap rounded-md bg-surface p-4 text-sm leading-6 text-graphite">
          {report.data.markdown}
        </pre>
      </section>
      <details className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <summary className="cursor-pointer font-semibold">Structured JSON</summary>
        <pre className="mt-4 overflow-auto rounded-md bg-surface p-4 text-xs text-graphite">
          {JSON.stringify(report.data, null, 2)}
        </pre>
      </details>
    </>
  );
}
