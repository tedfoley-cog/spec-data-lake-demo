"""Stage 5: Validate — cross-reference against existing data lake."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.models import DataLakeEntry, DocumentJob, PipelineStage

DATA_LAKE_ROOT = Path("data_lake")


def validate_entries(
    job: DocumentJob,
    entries: list[DataLakeEntry],
) -> list[dict[str, Any]]:
    """Validate new entries against existing data lake contents.

    Returns a list of validation findings (conflicts, duplicates, new references).
    """
    job.advance(PipelineStage.VALIDATING, f"Validating {len(entries)} entries against data lake")

    findings: list[dict[str, Any]] = []
    existing_ids = _load_existing_ids()

    new_count = 0
    update_count = 0
    conflict_count = 0

    for entry in entries:
        if entry.entry_id in existing_ids:
            existing = existing_ids[entry.entry_id]
            if existing.get("source_revision", "") != entry.source_revision:
                findings.append({
                    "type": "version_update",
                    "entry_id": entry.entry_id,
                    "old_revision": existing.get("source_revision", ""),
                    "new_revision": entry.source_revision,
                })
                update_count += 1
            else:
                findings.append({
                    "type": "duplicate",
                    "entry_id": entry.entry_id,
                    "message": "Entry already exists with same revision",
                })
                conflict_count += 1
        else:
            findings.append({
                "type": "new",
                "entry_id": entry.entry_id,
                "category": entry.category.value,
            })
            new_count += 1

    job.advance(
        PipelineStage.VALIDATING,
        f"Validation complete: {new_count} new, {update_count} updates, "
        f"{conflict_count} unchanged",
    )
    return findings


def _load_existing_ids() -> dict[str, dict[str, Any]]:
    """Load existing entry IDs from the data lake registry."""
    registry_path = DATA_LAKE_ROOT / "metadata" / "registry.json"
    if not registry_path.exists():
        return {}

    with open(registry_path) as f:
        registry = json.load(f)

    existing: dict[str, dict[str, Any]] = {}
    for doc in registry.get("documents", []):
        for entry in doc.get("entries", []):
            existing[entry["entry_id"]] = entry

    return existing
