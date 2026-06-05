"""Dashboard — FastAPI app with file upload, pipeline view, and data lake browser.

Runs on port 5001 inside the Devin VM. The presenter views it via the live
Browser tab. The audience watches documents flow through the pipeline stages
and into the structured data lake in real time.

Run::

    uv run uvicorn dashboard.app:app --host 0.0.0.0 --port 5001 --reload
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jira.webhook import router as jira_router
from pipeline import devin_session, repo_ingest
from pipeline.orchestrator import process_document

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "dashboard" / "state.json"
SESSIONS_FILE = REPO_ROOT / "dashboard" / "sessions.json"
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


def load_sessions() -> list[dict[str, Any]]:
    """Load the recorded Devin ingestion sessions."""
    if not SESSIONS_FILE.exists():
        return []
    with open(SESSIONS_FILE) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    sessions: list[dict[str, Any]] = data.get("sessions", [])
    return sessions


def save_sessions(sessions: list[dict[str, Any]]) -> None:
    """Persist the recorded Devin ingestion sessions."""
    SESSIONS_FILE.write_text(json.dumps({"sessions": sessions}, indent=2))


def _slug(value: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return out or "entry"


def _write_pulled_entries(lake: dict[str, list[dict[str, Any]]]) -> tuple[int, list[str]]:
    """Write data-lake files a session committed on its branch into the local lake."""
    total = 0
    categories: list[str] = []
    for category, files in lake.items():
        cat_dir = DATA_LAKE_ROOT / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        wrote_any = False
        for payload in files:
            source = payload.get("source_document") or "ingested"
            (cat_dir / f"{_slug(source)}.json").write_text(json.dumps(payload, indent=2))
            total += int(payload.get("entry_count", len(payload.get("entries", []))))
            wrote_any = True
        if wrote_any:
            categories.append(category)
    return total, categories


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
    documents = {
        f.get("source_document")
        for files in data_lake.values()
        for f in files
        if f.get("source_document")
    }
    completed_count = len(documents)

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


def _spawn_ingest_session(filename: str, content: bytes) -> dict[str, Any]:
    """Commit the dropped file to a fresh branch and launch a Devin session.

    This is the authentic flow: a real Devin session — not this process — runs
    the pipeline and commits the structured entries back to the branch.
    """
    branch = repo_ingest.make_branch_name(filename)
    base = repo_ingest.default_base()
    pushed = repo_ingest.push_dropped_file(filename, content, branch, base=base)
    created = devin_session.create_ingest_session(
        filename, branch, pushed["path"], repo=pushed["repo"], base=base
    )
    session = {
        "session_id": created.get("session_id", ""),
        "url": created.get("url", ""),
        "filename": filename,
        "branch": branch,
        "repo": pushed["repo"],
        "file_path": pushed["path"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "entries_pulled": False,
        "entry_count": 0,
        "categories": [],
    }
    sessions = load_sessions()
    sessions.append(session)
    save_sessions(sessions)
    return session


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> JSONResponse:
    """Upload a document for ingestion.

    When a Devin API token and a GitHub token are configured, dropping a file
    spins up a real Devin session that ingests it on a branch (the dashboard
    then reflects the committed entries). Otherwise the pipeline runs in-process
    so the app still works offline.
    """
    if not file.filename:
        return JSONResponse({"error": "No filename"}, status_code=400)

    content = await file.read()

    # Authentic flow: spin up a real Devin session to do the ingestion.
    if devin_session.sessions_enabled() and repo_ingest.git_enabled():
        try:
            session = _spawn_ingest_session(file.filename, content)
            return JSONResponse({"status": "session", "session": session})
        except Exception as e:  # noqa: BLE001 - surface and fall back locally
            # If the API/branch push fails, fall back to local processing below
            # so a live demo never dead-ends.
            fallback_error = str(e)
    else:
        fallback_error = ""

    # Fallback: run the pipeline in-process.
    dest_dir = SOURCE_DOCS / "uploads"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename
    dest_path.write_bytes(content)
    try:
        job = process_document(dest_path)
        return JSONResponse({
            "status": "success",
            "job": job.to_dict(),
            "fallback_error": fallback_error,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/sessions")
def api_sessions() -> dict[str, Any]:
    """Return recorded Devin ingestion sessions, refreshing live status.

    For each session that hasn't been reflected yet, this also checks the branch
    for committed ``data_lake/`` entries and pulls them into the local lake so the
    dashboard surfaces exactly what the Devin session produced.
    """
    sessions = load_sessions()
    changed = False
    for s in sessions:
        if devin_session.sessions_enabled() and s.get("session_id"):
            try:
                status = devin_session.get_session_status(s["session_id"])
                # v3: prefer the fine-grained status_detail (working/finished/…),
                # falling back to the coarse status (running/exit/error/…).
                new_status = status.get("status_detail") or status.get("status")
                if new_status and new_status != s.get("status") and not s.get("entries_pulled"):
                    s["status"] = new_status
                    changed = True
                if status.get("url") and not s.get("url"):
                    s["url"] = status["url"]
                    changed = True
                prs = status.get("pull_requests") or []
                if prs and prs[0].get("pr_url") and not s.get("pr_url"):
                    s["pr_url"] = prs[0]["pr_url"]
                    changed = True
            except Exception:  # noqa: BLE001 - status is best-effort
                pass
        if not s.get("entries_pulled") and repo_ingest.git_enabled():
            try:
                lake = repo_ingest.read_data_lake_from_branch(s["branch"], s.get("repo"))
            except Exception:  # noqa: BLE001 - branch read is best-effort
                lake = {}
            if lake:
                count, categories = _write_pulled_entries(lake)
                s["entries_pulled"] = True
                s["entry_count"] = count
                s["categories"] = categories
                s["status"] = "integrated"
                changed = True
    if changed:
        save_sessions(sessions)
    return {"sessions": sessions}


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
