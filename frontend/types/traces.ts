import type { QAExample } from "@/types/datasets";
import type { Experiment } from "@/types/experiments";

export type ModelResponse = {
  id: string;
  experiment_id?: string | null;
  qa_example_id: string;
  answer_text: string;
  answerability: string;
  confidence?: number | null;
  cited_chunk_ids: string[];
  retrieved_chunk_ids: string[];
  raw_model_output: Record<string, unknown>;
  latency_ms?: number | null;
  estimated_cost?: number | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  model_provider: string;
  model_name: string;
  prompt_template_id?: string | null;
  created_at: string;
};

export type EvaluationResult = {
  id: string;
  model_response_id: string;
  correctness_score?: number | null;
  groundedness_score?: number | null;
  citation_precision?: number | null;
  citation_recall?: number | null;
  retrieval_precision?: number | null;
  retrieval_recall?: number | null;
  refusal_score?: number | null;
  hallucination_flag: boolean;
  overall_score?: number | null;
  failure_type?: string | null;
  evaluator_name: string;
  evaluator_version: string;
  judge_explanation?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ClaimSupportClaim = {
  claim_index: number;
  claim_text: string;
  cited_chunk_ids: string[];
  support_status: "supported" | "partially_supported" | "unsupported" | "uncited" | string;
  token_overlap?: number | null;
  cited_chunks_retrieved: boolean;
};

export type ClaimSupportMetadata = {
  method?: string;
  claim_count?: number;
  supported_claim_count?: number;
  unsupported_claim_count?: number;
  uncited_claim_count?: number;
  claim_support_rate?: number | null;
  citation_coverage?: number | null;
  unsupported_claim_rate?: number | null;
  claims?: ClaimSupportClaim[];
};

export type FailureAnalysisMetadata = {
  primary_failure_type?: string;
  secondary_failure_types?: string[];
  failure_reason?: string;
  evidence_summary?: string;
  retrieval_failure?: boolean;
  generation_failure?: boolean;
};

export type HumanReview = {
  id: string;
  model_response_id: string;
  reviewer_name?: string | null;
  reviewer_role?: string | null;
  correctness_label?: string | null;
  groundedness_label?: string | null;
  refusal_label?: string | null;
  notes?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TraceChunk = {
  chunk_id: string;
  document_id: string;
  document_title: string;
  chunk_index: number;
  chunk_text: string;
  rank: number;
  similarity_score: number;
  was_cited: boolean;
};

export type ResponseTrace = {
  model_response: ModelResponse;
  qa_example: QAExample;
  experiment?: Experiment | null;
  evaluation?: EvaluationResult | null;
  retrieved_chunks: TraceChunk[];
  cited_chunks: TraceChunk[];
  prompt_template?: {
    id: string;
    name: string;
    version: string;
    template_type: string;
  } | null;
  human_reviews: HumanReview[];
};
