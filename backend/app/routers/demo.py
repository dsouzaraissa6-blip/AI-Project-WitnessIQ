"""
WitnessIQ Demo Data Router
Loads the pre-configured fictional demonstration case.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Case, Statement

router = APIRouter(prefix="/demo", tags=["demo"])

DEMO_CASE = {
    "title": "Jewellery Store Incident",
    "reference_id": "DEMO-001",
    "incident_date": "2026-01-15",
    "description": (
        "Reports concerning a person leaving a jewellery store following a suspected theft. "
        "FICTIONAL DATA — for demonstration purposes only."
    ),
    "is_demo": True,
}

DEMO_STATEMENTS = [
    {
        "witness_label": "Witness A",
        "content": (
            "I was standing across the road outside the jewellery store. "
            "At approximately 8:15 PM, I saw a man leave through the front entrance. "
            "He was wearing a black jacket and dark trousers. "
            "A red car was parked near the entrance. "
            "I could not see the driver's face."
        ),
    },
    {
        "witness_label": "Witness B",
        "content": (
            "I was standing near the bus stop across from the jewellery store. "
            "At around 8:45 PM, I noticed a man exiting through the front entrance. "
            "He appeared to be wearing a blue jacket and dark trousers. "
            "A red car was parked near the store entrance. "
            "I did not see the driver's face."
        ),
    },
    {
        "witness_label": "Witness C",
        "content": (
            "I was inside a nearby shop when I heard shouting at approximately 8:20 PM. "
            "I then noticed a person running toward the rear lane. "
            "I could not identify the person or determine what had happened inside the jewellery store."
        ),
    },
]


@router.post("/load")
async def load_demo_case(db: AsyncSession = Depends(get_db)):
    """
    Creates (or returns existing) the fictional demonstration case with three witness statements.
    Clearly labelled as fictional data.
    """
    # Check if already exists
    existing = await db.scalar(
        select(Case).where(Case.reference_id == DEMO_CASE["reference_id"])
    )
    if existing:
        # Return the existing demo case
        stmt_result = await db.execute(
            select(Statement).where(Statement.case_id == existing.id).order_by(Statement.created_at)
        )
        stmts = stmt_result.scalars().all()
        return {
            "case_id": existing.id,
            "message": "Demo case already exists. Returning existing case.",
            "statement_count": len(stmts),
        }

    # Create the case
    case = Case(**DEMO_CASE)
    db.add(case)
    await db.flush()
    await db.refresh(case)

    for stmt_data in DEMO_STATEMENTS:
        stmt = Statement(case_id=case.id, **stmt_data)
        db.add(stmt)

    await db.flush()

    stmt_result = await db.execute(
        select(Statement).where(Statement.case_id == case.id)
    )
    count = len(stmt_result.scalars().all())

    return {
        "case_id": case.id,
        "message": "Demo case loaded successfully. Data is entirely fictional.",
        "statement_count": count,
    }
