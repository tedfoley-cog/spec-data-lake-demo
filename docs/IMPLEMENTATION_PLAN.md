# Implementation Plan — Automotive Spec Data Lake

> Committed before the rest of the scaffold per the Demo Scaffold playbook (Step 2b).

## 1. What the demo proves

Devin can **continuously** ingest unstructured automotive engineering documents —
PDFs containing complex state machine diagrams, flow charts, and dense tables;
Excel requirements matrices; Word signal catalogs — and automatically parse,
classify, and structure them into a **well-defined data lake**. When a new
specification revision drops, Devin picks it up, spins up parallel sub-agents to
process each document, and integrates the structured output without human
intervention. This replaces a manual Ctrl+F-and-copy workflow that currently
takes an engineer ~1 week for root cause analysis.

## 2. What Devin does live (one sentence)

Devin is triggered from a Jira ticket, spins up child sessions to process
uploaded automotive spec documents in parallel, structures them into a data lake
with full traceability, creates Jira user stories for each finding, and the
presenter watches the entire pipeline progress live on a localhost dashboard.

## 3. Stack and rationale

| Layer | Choice | Why | Source |
|---|---|---|---|
| Domain | Powertrain Control Module (PCM) — power modes + transmission | Rich in state machines, flow diagrams, dense tables | SAE J1979; ISO 15031 |
| Document formats | PDF (state machines, tables, diagrams), Excel (requirements), Word (CAN signals, DTCs) | Three main unstructured formats from customer workflow | Customer discovery |
| Spec representation | Markdown + pre-extracted JSON + actual diagram PNGs | Real parsing requires proprietary tools; pre-extracted shows what the parser produces | PyMuPDF docs |
| Dashboard | FastAPI + Jinja2 + vanilla JS, port 5001 | Upload UI + real-time pipeline visualization + data lake browser | FastAPI docs |
| Data lake format | Structured JSON files organized by category | Lightweight, browsable, versionable — shows the "after" structure clearly | — |
| Child sessions | Devin MCP `devin_session_create` | Fan out document processing to parallel sub-agents | Devin API v3 |
| Jira integration | Jira REST API v3 | Trigger from Jira webhook, create user stories back | Atlassian REST API docs |
| CI | GitHub Actions: uv + ruff + mypy + pytest | Same shape as other tedfoley-cog demo repos | — |

## 4. Repo layout

```
README.md
DEMO_NOTES.md
.gitignore
.github/workflows/ci.yml
pyproject.toml

docs/
  IMPLEMENTATION_PLAN.md          # This file
  flowchart.html                  # Demo flow (Mermaid, standalone)
  flowchart.png                   # Rendered PNG for README

source_documents/
  pdf_specs/
    pcm_power_modes.md            # Spec content with state machine description
    pcm_power_modes.extracted.json
    transmission_shift_logic.md   # Spec content with flow diagram description
    transmission_shift_logic.extracted.json
    diagrams/
      pcm_state_machine.png       # Actual state machine diagram image
      shift_logic_flow.png        # Actual flow chart diagram image
      can_bus_topology.png        # CAN bus network topology diagram
  excel/
    system_requirements.xlsx      # Requirements matrix
    test_parameters.xlsx          # Calibration parameters
  word_docs/
    can_signal_catalog.md         # CAN signal definitions
    can_signal_catalog.extracted.json
    diagnostic_dtc_matrix.md      # DTC codes, conditions, actions
    diagnostic_dtc_matrix.extracted.json

pipeline/
  __init__.py
  models.py                       # Pipeline data models
  ingest.py                       # File reception and metadata extraction
  extract.py                      # Text, table, and diagram region extraction
  classify.py                     # Document type classification
  structure.py                    # Convert to data lake schema
  validate.py                     # Cross-reference validation
  integrate.py                    # Data lake integration with versioning
  orchestrator.py                 # Run full pipeline, update dashboard state

data_lake/
  signals/                        # Structured CAN signal definitions
  states/                         # State machine definitions
  requirements/                   # Structured requirements
  dtcs/                           # Diagnostic trouble codes
  parameters/                     # Calibration and test parameters
  relationships/                  # Cross-document links
  metadata/
    registry.json                 # Document registry and versions

dashboard/
  __init__.py
  app.py                          # FastAPI app with upload + pipeline view
  state.json                      # Pipeline state (stages, history)
  templates/
    index.html                    # Upload UI + pipeline + data lake browser
  static/
    style.css                     # Dashboard styling

jira/
  __init__.py
  client.py                       # Jira REST API client
  webhook.py                      # Jira webhook handler (FastAPI routes)
  stories.py                      # User story creation from pipeline findings

tests/
  conftest.py
  test_pipeline.py
  test_classify.py
  test_structure.py

scripts/
  generate_diagrams.py            # Generate source document diagrams
  generate_excel.py               # Generate Excel source documents
```

## 5. Flowchart outline

```
Trigger (Jira ticket / File upload)
  → Devin Orchestrator Session
    → Spin up Child Sessions (one per document type)
      → Child 1: Parse PDF specs (state machines, flow diagrams, tables)
      → Child 2: Parse Excel requirements
      → Child 3: Parse Word catalogs
    → Aggregate results
  → Pipeline Stages (visible on dashboard):
    1. Ingest — file received, metadata extracted
    2. Extract — text, tables, diagram regions identified
    3. Classify — document type and content categories
    4. Structure — convert to data lake schema
    5. Validate — cross-reference against existing data
    6. Integrate — add to data lake with version tracking
  → Jira Integration:
    → Create user stories for new findings
    → Update original ticket with results
  → Dashboard shows continuous processing history
```

## 6. Runtime plan

**Appears runnable via pre-extracted JSON.**
Real PDF/Word parsing would require proprietary tools; the demo uses
pre-extracted JSON files with markdown originals and actual diagram
images to show what the parser produces.

Commands:
- `uv run uvicorn dashboard.app:app --port 5001` — starts the upload dashboard
- Upload a file via the UI or API → pipeline runs → data lake populates
- `uv run python -m pipeline.orchestrator` — process all source documents
- Dashboard auto-refreshes to show pipeline progress

## 7. CI plan

GitHub Actions: checkout → install uv → uv sync → ruff check → mypy → pytest.
Under 50 lines of YAML.

## 8. Risks and unknowns

1. **Jira credentials**: Need user's Jira instance URL, project key, and API token.
   Scaffold includes a mock Jira client that logs API calls without hitting a real server.
2. **Child session creation**: Requires Devin API access; the demo playbook calls
   `devin_session_create` to fan out work. Without API access, falls back to
   sequential processing in a single session.
3. **Real PDF parsing**: Not implemented; pre-extracted JSON is used. Could wire in
   PyMuPDF/Camelot for live demos.
4. **Integration APIs (Jama, JFrog, SharePoint)**: Documented as longer-term vision.
   Current demo focuses on Jira only.
5. **Digital twin / continuous processing**: The "continuous" aspect is shown via the
   upload UI and processing history. True always-on file watching would need a
   background service or scheduled Devin sessions.
