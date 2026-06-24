export type ReviewerType =
  | "self"
  | "student"
  | "domain_reviewer"
  | "clinician"
  | "unknown";

export type ReviewStatus = "pending" | "completed" | "skipped";
export type Severity = "low" | "medium" | "high" | "critical";

export type RetrievedReviewChunk = {
  chunk_id: string;
  rank: number;
  was_cited: boolean;
  document_title: string;
  chunk_text: string;
};

export type AutomatedScores = {
  correctness_score?: number | null;
  groundedness_score?: number | null;
  citation_precision?: number | null;
  citation_recall?: number | null;
  retrieval_recall?: number | null;
  refusal_score?: number | null;
  overall_score?: number | null;
};

export type RichFailureTaxonomy = {
  schema_version?: string;
  legacy_failure_type?: string | null;
  primary_failure_category?: string | null;
  failure_categories?: string[];
  severity?: Severity | string | null;
  failure_stage?: string | null;
  safety_relevant_failure?: boolean;
  diagnostic_notes?: string[];
  category_metadata?: Record<string, unknown>[];
};

export type ManualReviewSnapshot = {
  review_id?: string;
  reviewer_label?: string | null;
  reviewer_type?: ReviewerType | string | null;
  review_status?: ReviewStatus | string | null;
  answer_correctness?: number | null;
  groundedness?: number | null;
  citation_quality?: number | null;
  refusal_safety?: number | null;
  should_refuse?: boolean | null;
  did_refuse?: boolean | null;
  selected_failure_categories?: string[];
  severity_override?: Severity | string | null;
  review_notes?: string | null;
  confidence?: number | null;
  reviewer_time_seconds?: number | null;
  adjudication_status?: string | null;
  sample?: boolean;
  sample_notes?: string | null;
};

export type ReviewQueueItem = {
  response_id: string;
  evaluation_id?: string | null;
  qa_example_id: string;
  qa_id?: string | null;
  question: string;
  gold_answer?: string | null;
  expected_answerability: string;
  generated_answer: string;
  model_answerability: string;
  cited_chunk_ids: string[];
  retrieved_chunks: RetrievedReviewChunk[];
  automated_scores: AutomatedScores;
  legacy_failure_type?: string | null;
  rich_failure_taxonomy?: RichFailureTaxonomy | null;
  manual_review?: ManualReviewSnapshot | null;
  review_template: ManualReviewSnapshot;
};

export type ReviewQueue = {
  metadata: Record<string, unknown>;
  experiment: {
    id: string;
    name: string;
    status?: string;
    model_provider?: string;
    model_name?: string;
    top_k?: number;
    metadata?: Record<string, unknown>;
  };
  items: ReviewQueueItem[];
};

export type ReviewSummaryRow = ManualReviewSnapshot & {
  review_id: string;
  response_id: string;
  automated_failure_categories: string[];
  has_override?: boolean;
  category_overlap_count?: number | null;
  category_jaccard?: number | null;
  exact_category_match?: boolean | null;
  severity_match?: boolean | null;
  refusal_decision_match?: boolean | null;
  sample?: boolean;
};

export type ReviewSummary = {
  metadata: Record<string, unknown>;
  experiment: ReviewQueue["experiment"];
  review_count: number;
  completed_review_count: number;
  rubric_averages: Record<string, number>;
  calibration: Record<string, number | string | boolean | null>;
  reviewer_failure_category_counts: Record<string, number>;
  reviewer_override_count: number;
  rows: ReviewSummaryRow[];
  limitations: string[];
  markdown: string;
};
