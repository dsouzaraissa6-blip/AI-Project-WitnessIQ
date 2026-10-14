"""
WitnessIQ Cases Router
CRUD endpoints for case management.
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from ..database import get_db
from ..models import Case, Statement, AnalysisResult
from ..schemas import CaseCreate, CaseResponse, CaseListResponse

router = APIRouter(prefix="/cases", tags=["cases"])


async def _case_to_response(case: Case, db: AsyncSession) -> CaseResponse:
    count = await db.scalar(
        select(func.count()).where(Statement.case_id == case.id)
    )
    return CaseResponse(
        id=case.id,
        title=case.title,
        reference_id=case.reference_id,
        incident_date=case.incident_date,
        description=case.description,
        created_at=case.created_at,
        updated_at=case.updated_at,
        is_demo=case.is_demo,
        statement_count=count or 0,
    )


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(payload: CaseCreate, db: AsyncSession = Depends(get_db)):
    # Check reference_id uniqueness
    existing = await db.scalar(select(Case).where(Case.reference_id == payload.reference_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A case with reference ID '{payload.reference_id}' already exists."
        )
    case = Case(
        title=payload.title,
        reference_id=payload.reference_id,
        incident_date=payload.incident_date,
        description=payload.description,
        is_demo=payload.is_demo,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return await _case_to_response(case, db)


@router.get("/", response_model=CaseListResponse)
async def list_cases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).order_by(Case.updated_at.desc()))
    cases = result.scalars().all()
    responses = [await _case_to_response(c, db) for c in cases]
    return CaseListResponse(cases=responses, total=len(responses))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return await _case_to_response(case, db)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db)):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    await db.delete(case)
