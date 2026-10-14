"""
WitnessIQ FastAPI Application
Main entry point: configures CORS, registers routers, initialises DB.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import cases, statements, analysis, demo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting WitnessIQ backend — initialising database…")
    await init_db()
    logger.info("Database ready.")
    yield
    logger.info("WitnessIQ backend shutting down.")


app = FastAPI(
    title="WitnessIQ API",
    description=(
        "AI-powered witness statement analysis and inconsistency detection. "
        "This tool flags potential textual discrepancies for human review. "
        "It does NOT determine guilt, credibility, or factual truth."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/api/v1")
app.include_router(statements.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "WitnessIQ",
        "version": "1.0.0",
        "status": "running",
        "disclaimer": (
            "This system flags potential textual discrepancies for human review. "
            "It does not determine truth, guilt, or credibility."
        ),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
