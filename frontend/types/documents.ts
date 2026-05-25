export type DocumentItem = {
  id: string;
  title: string;
  source_url?: string | null;
  source_type: string;
  organization_name?: string | null;
  document_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type DocumentDetail = DocumentItem & {
  raw_text: string;
  cleaned_text: string;
};

export type DocumentChunk = {
  id: string;
  document_id: string;
  chunk_index: number;
  chunk_text: string;
  token_count: number;
  char_start?: number | null;
  char_end?: number | null;
  page_number?: number | null;
  section_title?: string | null;
  embedding_model?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};
