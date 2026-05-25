export type Dataset = {
  id: string;
  name: string;
  description?: string | null;
  version: string;
  source: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type QAExample = {
  id: string;
  dataset_id: string;
  document_id?: string | null;
  question: string;
  gold_answer: string;
  answerability: "answerable" | "unanswerable" | "ambiguous" | string;
  category: string;
  difficulty: string;
  risk_level: string;
  expected_behavior?: string | null;
  reviewed_by_human: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EvidenceLink = {
  id: string;
  qa_example_id: string;
  chunk_id: string;
  evidence_role: string;
  notes?: string | null;
  created_at: string;
};
