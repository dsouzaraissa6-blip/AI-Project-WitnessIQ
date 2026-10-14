"""
WitnessIQ Statements Router
Endpoints for adding, retrieving, and deleting witness statements.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import Case, Statement
from ..schemas import StatementCreate, StatementResponse

router = APIRouter(prefix="/cases/{case_id}/statements", tags=["statements"])


async def _get_case_or_404(case_id: int, db: AsyncSession) -> Case:
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


@router.get("/", response_model=List[StatementResponse])
async def list_statements(case_id: int, db: AsyncSession = Depends(get_db)):
    await _get_case_or_404(case_id, db)
    result = await db.execute(
        select(Statement).where(Statement.case_id == case_id).order_by(Statement.created_at)
    )
    return result.scalars().all()


@router.post("/", response_model=StatementResponse, status_code=status.HTTP_201_CREATED)
async def add_statement(
    case_id: int,
    payload: StatementCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_case_or_404(case_id, db)
    stmt = Statement(
        case_id=case_id,
        witness_label=payload.witness_label,
        content=payload.content,
        filename=payload.filename,
    )
    db.add(stmt)
    await db.flush()
    await db.refresh(stmt)
    return stmt


@router.post("/upload", response_model=StatementResponse, status_code=status.HTTP_201_CREATED)
async def upload_statement(
    case_id: int,
    witness_label: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a .txt or .pdf file as a witness statement."""
    await _get_case_or_404(case_id, db)

    filename = file.filename or ""
    content_bytes = await file.read()

    if filename.lower().endswith(".txt"):
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = content_bytes.decode("latin-1")
    elif filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content_bytes))
            content = "\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Could not extract text from PDF: {exc}"
            )
    else:
        raise HTTPException(
            status_code=422,
            detail="Unsupported file type. Please upload a .txt or .pdf file."
        )

    if not content.strip():
        raise HTTPException(status_code=422, detail="Uploaded file contains no readable text.")

    stmt = Statement(
        case_id=case_id,
        witness_label=witness_label,
        content=content,
        filename=filename,
    )
    db.add(stmt)
    await db.flush()
    await db.refresh(stmt)
    return stmt


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_statement(case_id: int, statement_id: int, db: AsyncSession = Depends(get_db)):
    await _get_case_or_404(case_id, db)
    stmt = await db.get(Statement, statement_id)
    if not stmt or stmt.case_id != case_id:
        raise HTTPException(status_code=404, detail="Statement not found.")
    await db.delete(stmt)
