"""
WitnessIQ Database Models
SQLAlchemy ORM models for cases, statements, analysis results, and review decisions.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    reference_id = Column(String(100), unique=True, nullable=False)
    incident_date = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_demo = Column(Boolean, default=False)

    statements = relationship("Statement", back_populates="case", cascade="all, delete-orphan")
    analyses = relationship("AnalysisResult", back_populates="case", cascade="all, delete-orphan")


class Statement(Base):
    __tablename__ = "statements"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    witness_label = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    filename = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="statements")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(JSON, nullable=True)          # Summary statistics
    discrepancies = Column(JSON, nullable=True)    # List of discrepancy objects
    extracted_facts = Column(JSON, nullable=True)  # Extracted entities per statement
    semantic_matches = Column(JSON, nullable=True) # Sentence pairs with similarity
    model_info = Column(JSON, nullable=True)       # Models/methods used

    case = relationship("Case", back_populates="analyses")
    reviews = relationship("ReviewDecision", back_populates="analysis", cascade="all, delete-orphan")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    discrepancy_id = Column(String(100), nullable=False)  # UUID from discrepancy list
    decision = Column(String(50), nullable=False)         # relevant | not_meaningful | needs_investigation | uncertain
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis = relationship("AnalysisResult", back_populates="reviews")
