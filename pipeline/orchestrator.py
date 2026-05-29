"""Pipeline orchestrator — runs all stages and updates dashboard state."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from pipeline.classify import classify_document
from pipeline.extract import extract_content
from pipeline.ingest import ingest_file
from pipeline.integrate import integrate_to_data_lake
from pipeline.models import DocumentJob, PipelineStage
from pipeline.structure import structure_for_data_lake
from pipeline.validate import validate_entries

STATE_FILE = Path("dashboard/state.json")


def process_document(file_path: Path, update_state: bool = True) -> DocumentJob:
    """Process a single document through the full pipeline."""
    # Stage 1: Ingest
    job = ingest_file(file_path)
    if update_state:
        _update_dashboard_state(job)
    time.sleep(0.1)  # Brief pause for visual effect in dashboard

    # Stage 2: Extract
    extracted = extract_content(job, file_path)
    if update_state:
        _update_dashboard_state(job)
    time.sleep(0.1)

    # Stage 3: Classify
    categories = classify_document(job, extracted)
    if update_state:
        _update_dashboard_state(job)
    time.sleep(0.1)

    # Stage 4: Structure
    entries = structure_for_data_lake(job, extracted, categories)
    if update_state:
        _update_dashboard_state(job)
    time.sleep(0.1)

    # Stage 5: Validate
    findings = validate_entries(job, entries)
    if update_state:
        _update_dashboard_state(job)
    time.sleep(0.1)

    # Stage 6: Integrate
    integrate_to_data_lake(job, entries, findings)
    if update_state:
        _update_dashboard_state(job)

    return job


def process_all_documents(source_dir: Path) -> list[DocumentJob]:
    """Process all documents in the source directory."""
    jobs: list[DocumentJob] = []

    # Process JSON files (pre-extracted specs)
    for json_file in sorted(source_dir.rglob("*.extracted.json")):
        print(f"\nProcessing: {json_file.name}")
        job = process_document(json_file)
        jobs.append(job)
        _print_job_summary(job)

    # Process Excel files
    for xlsx_file in sorted(source_dir.rglob("*.xlsx")):
        print(f"\nProcessing: {xlsx_file.name}")
        job = process_document(xlsx_file)
        jobs.append(job)
        _print_job_summary(job)

    return jobs


def _update_dashboard_state(job: DocumentJob) -> None:
    """Update the dashboard state.json with current job status."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
    else:
        state = {"active_jobs": {}, "completed_jobs": [], "data_lake_summary": {}}

    if job.current_stage == PipelineStage.INTEGRATED:
        # Move to completed
        state["active_jobs"].pop(job.job_id, None)
        state["completed_jobs"].append(job.to_dict())
    else:
        state["active_jobs"][job.job_id] = job.to_dict()

    # Update data lake summary
    state["data_lake_summary"] = _get_data_lake_summary()

    STATE_FILE.write_text(json.dumps(state, indent=2))


def _get_data_lake_summary() -> dict[str, Any]:
    """Get summary statistics of the data lake."""
    data_lake = Path("data_lake")
    summary: dict[str, Any] = {"categories": {}, "total_files": 0, "total_entries": 0}

    for category_dir in sorted(data_lake.iterdir()):
        if not category_dir.is_dir() or category_dir.name == "metadata":
            continue
        json_files = list(category_dir.glob("*.json"))
        entry_count = 0
        for jf in json_files:
            try:
                with open(jf) as f:
                    data = json.load(f)
                entry_count += data.get("entry_count", 0)
            except (json.JSONDecodeError, OSError):
                pass
        summary["categories"][category_dir.name] = {
            "files": len(json_files),
            "entries": entry_count,
        }
        summary["total_files"] += len(json_files)
        summary["total_entries"] += entry_count

    return summary


def _print_job_summary(job: DocumentJob) -> None:
    """Print a summary of a completed job."""
    status = "PASS" if job.current_stage == PipelineStage.INTEGRATED else "FAIL"
    print(f"  [{status}] {job.job_id}: {job.filename}")
    print(f"    Categories: {', '.join(job.categories)}")
    print(f"    Entities: {job.extracted_entities}")
    print(f"    Data lake paths: {len(job.data_lake_paths)} files written")


def main() -> None:
    """CLI entrypoint: process all source documents."""
    source_dir = Path("source_documents")
    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1])

    print("=" * 60)
    print("Automotive Spec Data Lake — Document Processing Pipeline")
    print("=" * 60)

    jobs = process_all_documents(source_dir)

    print("\n" + "=" * 60)
    print(f"Pipeline complete: {len(jobs)} documents processed")
    summary = _get_data_lake_summary()
    print(f"Data lake: {summary['total_entries']} entries across "
          f"{summary['total_files']} files")
    for cat, info in summary.get("categories", {}).items():
        print(f"  {cat}: {info['entries']} entries ({info['files']} files)")
    print("=" * 60)


if __name__ == "__main__":
    main()
