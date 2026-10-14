# WitnessIQ

WitnessIQ is an academic document-assistance app for organizing witness statements and highlighting textual differences for human review. It does not determine what happened, assess credibility, or infer guilt.

## What it does

- Create and save cases in SQLite, then add statements by pasting text or uploading `.txt` and text-based `.pdf` files.
- Analyze saved statements through a FastAPI backend, preserving source passages and sentence references.
- Extract times and selected clothing, vehicle, and entrance details with explicit rules. spaCy NER is optional and is not installed by the lightweight setup.
- Find related sentence pairs with a pure-Python TF-IDF cosine similarity fallback. Sentence Transformers (`all-MiniLM-L6-v2`) is optional and is not installed by the lightweight setup. Similarity indicates possible linguistic relatedness, not factual agreement.
- Compare extracted values with deterministic rules and label results as potential inconsistencies, differences for review, similar details, or one-witness-only details.
- Save reviewer decisions and notes, revisit case history, and download CSV reports.
- Load a clearly labelled fictional demo case from the dashboard.

There is no external LLM API or contradiction-classification model. Model availability and the selected fallback are shown with analysis results; no confidence or accuracy claims are made.

## Project layout

```text
backend/
  app/
    nlp/                 # Entity extraction, semantic matching, comparison
    routers/             # Cases, statements, analysis, demo API
    database.py          # Async SQLite setup
    models.py            # SQLAlchemy models
    report_generator.py  # CSV and PDF exports
  tests/
frontend/
  src/
    api/                 # Axios client
    components/
    pages/
```

## Requirements

- Node.js and npm
- The Python version already active in your project environment. The backend dependencies below avoid the compiled NLP packages that failed to install with your Python 3.14 build.

## Run locally

Open two terminals from the project root. If your prompt already starts with `(.venv)`, that environment is active; use it directly.

### Backend

```powershell
python -m pip install -r backend\requirements.txt
cd backend
python -m uvicorn app.main:app --reload
```

The API and interactive API docs are available at `http://localhost:8000` and `http://localhost:8000/docs`. The SQLite database is created as `backend\witnessiq.db` when the backend starts.

### Frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`). Vite proxies `/api` requests to the local backend.

## Demo workflow

1. Start both services.
2. Open the frontend and select **Load Demo Case**.
3. In the case workspace, select **Analyze Statements**.
4. Review the discrepancy, semantic match, extracted facts, and model information tabs.
5. Expand an item to inspect its original source passages and record a review decision.
6. Download CSV or PDF from the results page.

The demo contains three fictional witness statements. It is intentionally not precomputed: the backend analyzes the stored statement text.

## Tests and build

Run the backend comparison tests from `backend`:

```powershell
python -m pytest tests -q
```

Type-check and build the frontend from `frontend`:

```powershell
npm run build
```

## Limitations

- Entity extraction is intentionally lightweight. Rule-based patterns cover only a small set of time, clothing, vehicle, and location details; the spaCy model is optional and must be installed separately to add NER.
- The lightweight setup uses pure-Python TF-IDF similarity. spaCy NER and Sentence Transformers are optional and require separately compatible packages/models.
- Semantic matching and rule-based comparisons can miss context, speaker references, negation, uncertainty, and events involving different people. Every flagged item is only a prompt for human review.
- Scanned/image-only PDFs are not OCR processed. CSV export is supported; PDF report export is not included in the lightweight Python 3.14 setup.
- There is no authentication or authorization. Do not put sensitive or real investigative material into this academic demonstration app.
