"""
WitnessIQ Pydantic Schemas
Request/response models for the FastAPI API layer.
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# ─── Case Schemas ────────────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    reference_id: str = Field(..., min_length=1, max_length=100)
    incident_date: Optional[str] = None
    description: Optional[str] = None
    is_demo: bool = False


class CaseResponse(BaseModel):
    id: int
    title: str
    reference_id: str
    incident_date: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_demo: bool
    statement_count: int = 0

    class Config:
        orm_mode = True


class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    total: int


# ─── Statement Schemas ────────────────────────────────────────────────────────

class StatementCreate(BaseModel):
    witness_label: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10)
    filename: Optional[str] = None


class StatementResponse(BaseModel):
    id: int
    case_id: int
    witness_label: str
    content: str
    filename: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


# ─── Analysis Schemas ─────────────────────────────────────────────────────────

class AnalysisSummary(BaseModel):
    statements_analyzed: int
    related_pairs_found: int
    discrepancies_flagged: int
    unique_details_count: int
    analysis_method: str
    model_status: Dict[str, Any]


class ExtractedFact(BaseModel):
    statement_id: int
    witness_label: str
    entity_type: str       # PERSON, LOC, DATE, TIME, ORG, COLOR, OBJECT, ACTION
    value: str
    sentence: str
    sentence_index: int
    source: str            # "spacy_ner" | "rule_based" | "dateutil"


class SemanticMatch(BaseModel):
    statement_a_id: int
    statement_b_id: int
    witness_a: str
    witness_b: str
    sentence_a: str
    sentence_b: str
    sentence_a_index: int
    sentence_b_index: int
    similarity_score: float
    match_method: str      # "sentence_transformer" | "tfidf_cosine"


class DiscrepancyItem(BaseModel):
    id: str                # UUID
    category: str          # Time | Color | Location | Person | Object | Action | General
    witness_a_label: str
    witness_b_label: str
    witness_a_text: str
    witness_b_text: str
    witness_a_sentence: str
    witness_b_sentence: str
    witness_a_sentence_idx: int
    witness_b_sentence_idx: int
    classification: str    # potential_inconsistency | difference_for_review | one_witness_only | similar | ambiguous
    explanation: str
    detection_method: str  # "rule_based" | "ml_assisted" | "combined"
    similarity_score: Optional[float] = None
    review_status: Optional[str] = None  # None | relevant | not_meaningful | needs_investigation | uncertain
    review_note: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    id: int
    case_id: int
    created_at: datetime
    summary: AnalysisSummary
    discrepancies: List[DiscrepancyItem]
    extracted_facts: List[ExtractedFact]
    semantic_matches: List[SemanticMatch]
    model_info: Dict[str, Any]

    class Config:
        orm_mode = True


# ─── Review Schemas ───────────────────────────────────────────────────────────

class ReviewUpdate(BaseModel):
    decision: str = Field(..., regex="^(relevant|not_meaningful|needs_investigation|uncertain)$")
    note: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    analysis_id: int
    discrepancy_id: str
    decision: str
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ─── Report Schemas ───────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    format: str = Field("csv", regex="^(csv|pdf)$")
