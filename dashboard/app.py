"""Dashboard — FastAPI app with file upload, pipeline view, and data lake browser.

Runs on port 5001 inside the Devin VM. The presenter views it via the live
Browser tab. The audience watches documents flow through the pipeline stages
and into the structured data lake in real time.

Run::

    uv run uvicorn dashboard.app:app --host 0.0.0.0 --port 5001 --reload
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jira.webhook import router as jira_router
from pipeline.orchestrator import process_document

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "dashboard" / "state.json"
DATA_LAKE_ROOT = REPO_ROOT / "data_lake"
SOURCE_DOCS = REPO_ROOT / "source_documents"
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

app = FastAPI(title="Automotive Spec Data Lake")
app.include_router(jira_router)
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)
app.mount(
    "/diagrams",
    StaticFiles(directory=str(SOURCE_DOCS / "pdf_specs" / "diagrams")),
    name="diagrams",
)


def load_state() -> dict[str, Any]:
    """Load the current pipeline state."""
    if not STATE_FILE.exists():
        return {"active_jobs": {}, "completed_jobs": [], "data_lake_summary": {}}
    with open(STATE_FILE) as f:
        state: dict[str, Any] = json.load(f)
    return state


def get_data_lake_contents() -> dict[str, Any]:
    """Get the full data lake contents for the browser view."""
    contents: dict[str, Any] = {}
    for category_dir in sorted(DATA_LAKE_ROOT.iterdir()):
        if not category_dir.is_dir() or category_dir.name == "metadata":
            continue
        cat_entries: list[dict[str, Any]] = []
        for jf in sorted(category_dir.glob("*.json")):
            try:
                with open(jf) as f:
                    data = json.load(f)
                cat_entries.append({
                    "filename": jf.name,
                    "source_document": data.get("source_document", ""),
                    "entry_count": data.get("entry_count", 0),
                    "integrated_at": data.get("integrated_at", ""),
                    "entries": data.get("entries", []),
                })
            except (json.JSONDecodeError, OSError):
                pass
        if cat_entries:
            contents[category_dir.name] = cat_entries
    return contents


def get_source_documents() -> list[dict[str, Any]]:
    """List available source documents with their diagrams."""
    docs: list[dict[str, Any]] = []
    for json_file in sorted(SOURCE_DOCS.rglob("*.extracted.json")):
        with open(json_file) as f:
            data = json.load(f)
        docs.append({
            "filename": json_file.name,
            "path": str(json_file.relative_to(REPO_ROOT)),
            "title": data.get("title", json_file.stem),
            "document_id": data.get("document_id", ""),
            "revision": data.get("revision", ""),
            "diagrams": data.get("diagrams", []),
            "tables": data.get("tables", 0),
        })
    for xlsx_file in sorted(SOURCE_DOCS.rglob("*.xlsx")):
        docs.append({
            "filename": xlsx_file.name,
            "path": str(xlsx_file.relative_to(REPO_ROOT)),
            "title": xlsx_file.stem.replace("_", " ").title(),
            "document_id": "",
            "revision": "",
            "diagrams": [],
            "tables": 1,
        })
    return docs


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Main dashboard page."""
    state = load_state()
    data_lake = get_data_lake_contents()
    source_docs = get_source_documents()

    # Count totals
    total_entries = sum(
        sum(f["entry_count"] for f in files)
        for files in data_lake.values()
    )
    total_categories = len(data_lake)
    completed_count = len(state.get("completed_jobs", []))

    return TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "state": state,
            "data_lake": data_lake,
            "source_docs": source_docs,
            "total_entries": total_entries,
            "total_categories": total_categories,
            "completed_count": completed_count,
        },
    )


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> JSONResponse:
    """Upload a document for pipeline processing."""
    if not file.filename:
        return JSONResponse({"error": "No filename"}, status_code=400)

    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(file.filename).suffix
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    # Also save to source_documents for persistence
    dest_dir = SOURCE_DOCS / "uploads"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename
    shutil.copy2(tmp_path, dest_path)

    # Process through pipeline
    try:
        job = process_document(dest_path)
        return JSONResponse({
            "status": "success",
            "job": job.to_dict(),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        tmp_path.unlink(missing_ok=True)


@app.get("/api/state")
def api_state() -> dict[str, Any]:
    """Get current pipeline state as JSON."""
    return load_state()


@app.get("/api/data-lake")
def api_data_lake() -> dict[str, Any]:
    """Get data lake contents as JSON."""
    return get_data_lake_contents()


@app.get("/api/data-lake/{category}")
def api_data_lake_category(category: str) -> Any:
    """Get entries for a specific data lake category."""
    cat_dir = DATA_LAKE_ROOT / category
    if not cat_dir.exists():
        return JSONResponse({"error": "Category not found"}, status_code=404)

    entries: list[dict[str, Any]] = []
    for jf in sorted(cat_dir.glob("*.json")):
        with open(jf) as f:
            data = json.load(f)
        entries.extend(data.get("entries", []))
    return {"category": category, "entries": entries, "count": len(entries)}


@app.post("/api/process-all")
def process_all_source_docs() -> JSONResponse:
    """Process all source documents through the pipeline."""
    from pipeline.orchestrator import process_all_documents

    jobs = process_all_documents(SOURCE_DOCS)
    return JSONResponse({
        "status": "success",
        "processed": len(jobs),
        "jobs": [j.to_dict() for j in jobs],
    })
