export type Experiment = {
  id: string;
  name: string;
  dataset_id: string;
  description?: string | null;
  model_provider: string;
  model_name: string;
  embedding_model: string;
  prompt_template_id?: string | null;
  retrieval_strategy: string;
  top_k: number;
  temperature: number;
  status: "draft" | "running" | "completed" | "failed" | string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ExperimentResults = {
  experiment_id: string;
  status: string;
  example_count: number;
  avg_correctness?: number | null;
  avg_groundedness?: number | null;
  avg_citation_precision?: number | null;
  avg_citation_recall?: number | null;
  avg_retrieval_precision?: number | null;
  avg_retrieval_recall?: number | null;
  refusal_accuracy?: number | null;
  hallucination_rate?: number | null;
  failure_type_counts: Record<string, number>;
  avg_latency_ms?: number | null;
  total_estimated_cost?: number | null;
};

export type ExperimentResponseRow = {
  response_id: string;
  qa_example_id: string;
  question: string;
  expected_answerability: string;
  model_answerability: string;
  answer_text: string;
  correctness_score?: number | null;
  groundedness_score?: number | null;
  hallucination_flag?: boolean | null;
  failure_type?: string | null;
  created_at: string;
};

export type ExperimentFailureRow = ExperimentResponseRow & {
  failure_reason: string;
};

export type ExperimentReport = {
  experiment: Experiment;
  results: ExperimentResults;
  failure_examples: ExperimentFailureRow[];
  markdown: string;
  generated_at: string;
  disclaimer: string;
  metadata: Record<string, unknown>;
};
