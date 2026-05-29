"""Stage 6: Integrate — write structured entries to the data lake."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.models import DataLakeEntry, DocumentJob, PipelineStage

DATA_LAKE_ROOT = Path("data_lake")


def integrate_to_data_lake(
    job: DocumentJob,
    entries: list[DataLakeEntry],
    findings: list[dict[str, Any]],
) -> list[str]:
    """Write validated entries to the data lake and update registry.

    Returns list of data lake paths that were written.
    """
    job.advance(PipelineStage.INTEGRATED, f"Integrating {len(entries)} entries into data lake")

    written_paths: list[str] = []

    # Group entries by category
    by_category: dict[str, list[DataLakeEntry]] = {}
    for entry in entries:
        cat = entry.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(entry)

    # Write each category file
    for category, cat_entries in by_category.items():
        cat_dir = DATA_LAKE_ROOT / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        # Use source document as the filename
        source_doc = cat_entries[0].source_document if cat_entries else "unknown"
        safe_name = source_doc.replace("/", "_").replace(" ", "_").lower()
        output_path = cat_dir / f"{safe_name}.json"

        data = {
            "source_document": source_doc,
            "source_revision": cat_entries[0].source_revision if cat_entries else "",
            "integrated_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(cat_entries),
            "entries": [e.to_dict() for e in cat_entries],
        }

        output_path.write_text(json.dumps(data, indent=2))
        rel_path = str(output_path)
        written_paths.append(rel_path)

    # Update registry
    _update_registry(job, entries, findings)

    job.data_lake_paths = written_paths
    job.advance(
        PipelineStage.INTEGRATED,
        f"Integrated into data lake: {len(written_paths)} files written",
    )
    return written_paths


def _update_registry(
    job: DocumentJob,
    entries: list[DataLakeEntry],
    findings: list[dict[str, Any]],
) -> None:
    """Update the data lake registry with new document processing record."""
    registry_path = DATA_LAKE_ROOT / "metadata" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {
            "data_lake_version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "documents": [],
            "total_entries": 0,
            "processing_history": [],
        }

    # Add document record
    doc_record = {
        "job_id": job.job_id,
        "filename": job.filename,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "categories": job.categories,
        "entries": [
            {
                "entry_id": e.entry_id,
                "category": e.category.value,
                "source_revision": e.source_revision,
            }
            for e in entries
        ],
    }
    registry["documents"].append(doc_record)
    registry["total_entries"] = sum(
        len(doc.get("entries", [])) for doc in registry["documents"]
    )

    # Add to processing history
    new_count = sum(1 for f in findings if f["type"] == "new")
    update_count = sum(1 for f in findings if f["type"] == "version_update")
    registry["processing_history"].append({
        "job_id": job.job_id,
        "filename": job.filename,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "new_entries": new_count,
        "updated_entries": update_count,
        "total_entries": len(entries),
    })

    registry_path.write_text(json.dumps(registry, indent=2))
