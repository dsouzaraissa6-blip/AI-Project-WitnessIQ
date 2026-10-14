"""
WitnessIQ Analysis Router
Endpoints for running analysis, retrieving results, human review, and reports.
"""
import json
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io

from ..database import get_db
from ..models import Case, Statement, AnalysisResult, ReviewDecision
from ..schemas import AnalysisResultResponse, AnalysisSummary, ReviewUpdate, ReviewResponse
from ..nlp.analyzer import analyze_statements
from ..report_generator import generate_csv_report, generate_pdf_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cases/{case_id}", tags=["analysis"])


async def _get_case_or_404(case_id: int, db: AsyncSession) -> Case:
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def _build_analysis_response(analysis: AnalysisResult) -> dict:
    """Convert ORM AnalysisResult to response dict."""
    summary_data = analysis.summary or {}
    return {
        "id": analysis.id,
        "case_id": analysis.case_id,
        "created_at": analysis.created_at,
        "summary": summary_data,
        "discrepancies": analysis.discrepancies or [],
        "extracted_facts": analysis.extracted_facts or [],
        "semantic_matches": analysis.semantic_matches or [],
        "model_info": analysis.model_info or {},
    }


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def run_analysis(case_id: int, db: AsyncSession = Depends(get_db)):
    """
    Trigger full NLP analysis on all statements in the case.
    Returns the analysis result immediately (synchronous for now).
    """
    case = await _get_case_or_404(case_id, db)

    # Load statements
    result = await db.execute(
        select(Statement).where(Statement.case_id == case_id).order_by(Statement.created_at)
    )
    statements = result.scalars().all()

    if len(statements) < 2:
        raise HTTPException(
            status_code=422,
            detail="At least two witness statements are required before running analysis."
        )

    stmt_data = [
        {"id": s.id, "witness_label": s.witness_label, "content": s.content}
        for s in statements
    ]

    try:
        analysis_output = analyze_statements(stmt_data)
    except Exception as exc:
        logger.exception("Analysis failed for case %d: %s", case_id, exc)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}")

    # Save to DB (replace previous analysis for this case)
    existing = await db.execute(
        select(AnalysisResult).where(AnalysisResult.case_id == case_id)
        .order_by(AnalysisResult.created_at.desc()).limit(1)
    )
    old_analysis = existing.scalar_one_or_none()
    if old_analysis:
        await db.delete(old_analysis)
        await db.flush()

    db_analysis = AnalysisResult(
        case_id=case_id,
        summary=analysis_output["summary"],
        discrepancies=analysis_output["discrepancies"],
        extracted_facts=analysis_output["extracted_facts"],
        semantic_matches=analysis_output["semantic_matches"],
        model_info=analysis_output["model_info"],
    )
    db.add(db_analysis)
    await db.flush()
    await db.refresh(db_analysis)

    return _build_analysis_response(db_analysis)


@router.get("/analysis", status_code=200)
async def get_analysis(case_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve the most recent analysis result for a case."""
    await _get_case_or_404(case_id, db)
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.case_id == case_id)
        .order_by(AnalysisResult.created_at.desc()).limit(1)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this case. Run analysis first.")

    # Load review decisions and merge
    review_result = await db.execute(
        select(ReviewDecision).where(ReviewDecision.analysis_id == analysis.id)
    )
    reviews = {r.discrepancy_id: r for r in review_result.scalars().all()}

    response = _build_analysis_response(analysis)
    # Merge review decisions into discrepancies
    for disc in response["discrepancies"]:
        rev = reviews.get(disc["id"])
        if rev:
            disc["review_status"] = rev.decision
            disc["review_note"] = rev.note
    return response


# ─── Human Review ─────────────────────────────────────────────────────────────

@router.post("/analysis/review/{discrepancy_id}", response_model=ReviewResponse)
async def submit_review(
    case_id: int,
    discrepancy_id: str,
    payload: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Submit or update a human-review decision for a flagged discrepancy."""
    await _get_case_or_404(case_id, db)

    # Get latest analysis
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.case_id == case_id)
        .order_by(AnalysisResult.created_at.desc()).limit(1)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found.")

    # Verify discrepancy_id exists in analysis
    disc_ids = [d["id"] for d in (analysis.discrepancies or [])]
    if discrepancy_id not in disc_ids:
        raise HTTPException(status_code=404, detail="Discrepancy not found in analysis.")

    # Upsert review decision
    rev_result = await db.execute(
        select(ReviewDecision).where(
            ReviewDecision.analysis_id == analysis.id,
            ReviewDecision.discrepancy_id == discrepancy_id,
        )
    )
    review = rev_result.scalar_one_or_none()

    if review:
        review.decision = payload.decision
        review.note = payload.note
        review.updated_at = datetime.utcnow()
    else:
        review = ReviewDecision(
            analysis_id=analysis.id,
            discrepancy_id=discrepancy_id,
            decision=payload.decision,
            note=payload.note,
        )
        db.add(review)

    await db.flush()
    await db.refresh(review)
    return review


# ─── Report Download ──────────────────────────────────────────────────────────

@router.get("/report")
async def download_report(
    case_id: int,
    format: str = "csv",
    db: AsyncSession = Depends(get_db),
):
    """Download analysis report as CSV or PDF."""
    case = await _get_case_or_404(case_id, db)

    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.case_id == case_id)
        .order_by(AnalysisResult.created_at.desc()).limit(1)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found.")

    case_dict = {
        "title": case.title,
        "reference_id": case.reference_id,
        "incident_date": case.incident_date,
        "description": case.description,
    }
    analysis_dict = {
        "summary": analysis.summary,
        "discrepancies": analysis.discrepancies,
        "extracted_facts": analysis.extracted_facts,
        "semantic_matches": analysis.semantic_matches,
    }

    if format == "pdf":
        try:
            content = generate_pdf_report(case_dict, analysis_dict)
        except ImportError as exc:
            raise HTTPException(
                status_code=501,
                detail="PDF export is not installed in this lightweight setup. Download the CSV report instead.",
            ) from exc
        media_type = "application/pdf"
        filename = f"witnessiq_report_{case.reference_id}.pdf"
    else:
        content = generate_csv_report(case_dict, analysis_dict)
        media_type = "text/csv"
        filename = f"witnessiq_report_{case.reference_id}.csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
