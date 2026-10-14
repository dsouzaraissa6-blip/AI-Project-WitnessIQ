// WitnessIQ — API type definitions

export interface Case {
  id: number;
  title: string;
  reference_id: string;
  incident_date?: string;
  description?: string;
  created_at: string;
  updated_at: string;
  is_demo: boolean;
  statement_count: number;
}

export interface Statement {
  id: number;
  case_id: number;
  witness_label: string;
  content: string;
  filename?: string;
  created_at: string;
}

export interface ExtractedFact {
  statement_id: number;
  witness_label: string;
  entity_type: string;
  value: string;
  sentence: string;
  sentence_index: number;
  source: string;
}

export interface SemanticMatch {
  statement_a_id: number;
  statement_b_id: number;
  witness_a: string;
  witness_b: string;
  sentence_a: string;
  sentence_b: string;
  sentence_a_index: number;
  sentence_b_index: number;
  similarity_score: number;
  match_method: string;
}

export type Classification =
  | 'potential_inconsistency'
  | 'difference_for_review'
  | 'one_witness_only'
  | 'similar'
  | 'ambiguous';

export type ReviewStatus =
  | 'relevant'
  | 'not_meaningful'
  | 'needs_investigation'
  | 'uncertain'
  | null;

export interface DiscrepancyItem {
  id: string;
  category: string;
  witness_a_label: string;
  witness_b_label: string;
  witness_a_text: string;
  witness_b_text: string;
  witness_a_sentence: string;
  witness_b_sentence: string;
  witness_a_sentence_idx: number;
  witness_b_sentence_idx: number;
  classification: Classification;
  explanation: string;
  detection_method: string;
  similarity_score?: number;
  review_status: ReviewStatus;
  review_note?: string;
}

export interface AnalysisSummary {
  statements_analyzed: number;
  related_pairs_found: number;
  discrepancies_flagged: number;
  unique_details_count: number;
  analysis_method: string;
  model_status: Record<string, unknown>;
}

export interface AnalysisResult {
  id: number;
  case_id: number;
  created_at: string;
  summary: AnalysisSummary;
  discrepancies: DiscrepancyItem[];
  extracted_facts: ExtractedFact[];
  semantic_matches: SemanticMatch[];
  model_info: Record<string, unknown>;
}

export interface ReviewUpdate {
  decision: ReviewStatus;
  note?: string;
}
