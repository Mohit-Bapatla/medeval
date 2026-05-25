import type { ExperimentResults } from "@/types/experiments";

export type DashboardSummary = {
  counts: {
    documents: number;
    chunks: number;
    datasets: number;
    qa_examples: number;
    experiments: number;
    model_responses: number;
    evaluation_results: number;
  };
  latest_experiment?: {
    id: string;
    name: string;
    status: string;
    created_at: string;
    results: ExperimentResults;
  } | null;
  status_note: string;
};
