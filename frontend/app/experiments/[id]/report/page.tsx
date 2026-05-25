"use client";

import { useParams } from "next/navigation";
import { useState } from "react";

import { DisclaimerCallout } from "@/components/ui/disclaimer-callout";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { API_BASE_URL } from "@/lib/api";
import { formatDate, formatMetric } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import type { ExperimentReport } from "@/types/experiments";

export default function ExperimentReportPage() {
  const params = useParams<{ id: string }>();
  const report = useApi<ExperimentReport>(
    params.id ? `/experiments/${params.id}/report` : null,
  );
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

  function downloadJson() {
    if (!report.data) {
      return;
    }
    const blob = new Blob([JSON.stringify(report.data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${report.data.experiment.name.replaceAll(" ", "_")}_report.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function downloadCsv() {
    if (!params.id) {
      return;
    }
    window.location.href = `${API_BASE_URL}/experiments/${params.id}/results.csv`;
  }

  async function copyMarkdown() {
    if (!report.data) {
      return;
    }
    await navigator.clipboard.writeText(report.data.markdown);
    setMessage("Markdown copied to clipboard.");
    setTimeout(() => setMessage(null), 3000);
  }

  if (report.loading) {
    return <LoadingState label="Loading report..." />;
  }
  if (report.error) {
    return <ErrorState message={report.error} />;
  }
  if (!report.data) {
    return (
      <EmptyState
        title="Report not found"
        message="The backend did not return this report."
        showSeedCommands={false}
      />
    );
  }

  const hallucinationRate = report.data.results.hallucination_rate;

  return (
    <>
      <PageHeader
        title={`Report: ${report.data.experiment.name}`}
        description="Computed local evaluation summary. Preview, copy, or export. Not a validated benchmark report."
        action={
          <div className="flex flex-wrap gap-2">
            <button
              className="rounded-md border border-line bg-white px-3 py-2 text-xs font-medium text-graphite shadow-sm transition-colors hover:border-graphite hover:text-ink"
              onClick={() => void copyMarkdown()}
              type="button"
            >
              Copy .md
            </button>
            <button
              className="rounded-md border border-line bg-white px-3 py-2 text-xs font-medium text-graphite shadow-sm transition-colors hover:border-graphite hover:text-ink"
              onClick={downloadJson}
              type="button"
            >
              Download JSON
            </button>
            <button
              className="rounded-md border border-line bg-white px-3 py-2 text-xs font-medium text-graphite shadow-sm transition-colors hover:border-graphite hover:text-ink"
              onClick={downloadCsv}
              type="button"
            >
              Download CSV
            </button>
            <button
              className="rounded-md bg-clinical px-3 py-2 text-xs font-medium text-white shadow-sm transition-opacity hover:opacity-90"
              onClick={downloadMarkdown}
              type="button"
            >
              Download .md
            </button>
          </div>
        }
      />

      {message ? (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-success/30 bg-success/5 px-4 py-3 text-sm text-success">
          ✓ {message}
        </div>
      ) : null}

      {/* Metric summary */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Examples evaluated"
          value={report.data.results.example_count}
        />
        <MetricCard
          label="Avg correctness"
          value={formatMetric(report.data.results.avg_correctness)}
          accent={
            report.data.results.avg_correctness != null
              ? report.data.results.avg_correctness >= 0.75
                ? "success"
                : report.data.results.avg_correctness >= 0.5
                  ? "warning"
                  : "danger"
              : undefined
          }
        />
        <MetricCard
          label="Avg groundedness"
          value={formatMetric(report.data.results.avg_groundedness)}
          accent={
            report.data.results.avg_groundedness != null
              ? report.data.results.avg_groundedness >= 0.75
                ? "success"
                : report.data.results.avg_groundedness >= 0.5
                  ? "warning"
                  : "danger"
              : undefined
          }
        />
        <MetricCard
          label="Hallucination rate"
          value={formatMetric(hallucinationRate)}
          accent={
            hallucinationRate != null
              ? hallucinationRate > 0.3
                ? "danger"
                : hallucinationRate > 0.1
                  ? "warning"
                  : "success"
              : undefined
          }
        />
      </div>

      {/* Metadata + disclaimer */}
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-graphite">
          Report metadata
        </h2>
        <div className="mt-3 flex flex-wrap gap-6 text-sm">
          <div>
            <p className="text-xs text-graphite">Generated</p>
            <p className="mt-0.5 font-medium text-ink">
              {formatDate(report.data.generated_at)}
            </p>
          </div>
          <div>
            <p className="text-xs text-graphite">Experiment</p>
            <p className="mt-0.5 font-medium text-ink">
              {report.data.experiment.name}
            </p>
          </div>
        </div>
      </section>

      <div className="mt-4">
        <DisclaimerCallout message={report.data.disclaimer} />
      </div>

      {/* Markdown preview */}
      <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-ink">Markdown preview</h2>
          <button
            className="rounded-md border border-line px-2.5 py-1 text-xs font-medium text-graphite hover:border-clinical hover:text-clinical transition-colors"
            onClick={() => void copyMarkdown()}
            type="button"
          >
            Copy
          </button>
        </div>
        <pre className="max-h-[640px] overflow-auto whitespace-pre-wrap rounded-md bg-surface p-4 text-xs leading-6 text-graphite font-mono">
          {report.data.markdown}
        </pre>
      </section>

      {/* Structured JSON */}
      <details className="mt-5 rounded-lg border border-line bg-white shadow-sm">
        <summary className="cursor-pointer select-none px-5 py-4 text-sm font-semibold text-ink hover:text-clinical">
          Structured JSON
          <span className="ml-2 text-xs font-normal text-graphite">
            (click to expand)
          </span>
        </summary>
        <div className="border-t border-line px-5 pb-5 pt-4">
          <pre className="overflow-auto rounded-md bg-surface p-4 text-xs leading-5 text-graphite font-mono">
            {JSON.stringify(report.data, null, 2)}
          </pre>
        </div>
      </details>
    </>
  );
}
