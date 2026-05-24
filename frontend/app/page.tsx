import { ApiStatusPanel } from "@/components/api-status";

const plannedMetrics = [
  "correctness",
  "groundedness",
  "hallucination rate",
  "citation accuracy",
  "refusal accuracy",
  "retrieval recall",
  "latency",
  "cost",
];

const workflow = [
  "Import evaluation datasets",
  "Run retrieval and answer-generation experiments",
  "Store traces, citations, metrics, and failures",
  "Compare reports across model and retrieval settings",
];

export default function Home() {
  return (
    <main className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase text-clinical">MedEval</p>
            <h1 className="mt-3 text-4xl font-semibold text-ink md:text-5xl">
              Healthcare RAG evaluation and reliability platform
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-graphite">
              Open-source tooling for evaluating healthcare RAG and LLM systems across
              correctness, grounding, citation behavior, refusals, retrieval quality,
              latency, and cost.
            </p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-4 text-sm text-graphite">
            <p className="font-semibold text-ink">Development foundation</p>
            <p className="mt-2 max-w-xs">
              This early build contains the app structure, API health checks, and local
              development wiring. It does not contain validated benchmark results.
            </p>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
          <h2 className="text-xl font-semibold text-ink">Evaluation focus</h2>
          <p className="mt-3 text-sm leading-6 text-graphite">
            MedEval is not a generic chatbot. The project is organized around reproducible
            experiments, traces, metrics, dataset schemas, reports, and reliability review.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {plannedMetrics.map((metric) => (
              <div key={metric} className="rounded-md border border-line bg-surface px-3 py-2">
                <span className="text-sm font-medium text-ink">{metric}</span>
              </div>
            ))}
          </div>
        </section>

        <ApiStatusPanel />

        <section className="rounded-lg border border-line bg-white p-5 shadow-sm lg:col-span-2">
          <h2 className="text-xl font-semibold text-ink">Planned workflow</h2>
          <div className="mt-5 grid gap-3 md:grid-cols-4">
            {workflow.map((item, index) => (
              <div key={item} className="rounded-md border border-line bg-surface p-4">
                <p className="text-sm font-semibold text-clinical">Step {index + 1}</p>
                <p className="mt-2 text-sm leading-6 text-graphite">{item}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
