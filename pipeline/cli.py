"""Command-line entrypoint for ingesting a single document.

This is the deterministic command a spawned Devin ingestion session runs against
a dropped file::

    uv run python -m pipeline.cli source_documents/dropped/<file>

It runs the full 6-stage pipeline, writing structured entries into
``data_lake/<category>/`` and updating ``dashboard/state.json`` — exactly what
the session then commits back to its ``ingest/<doc>-<ts>`` branch.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.models import PipelineStage
from pipeline.orchestrator import process_document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest a document into the spec data lake.")
    parser.add_argument("file", help="Path to the document to ingest (relative to the repo root).")
    args = parser.parse_args(argv)

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 2

    job = process_document(file_path)

    total = sum(job.extracted_entities.values()) if job.extracted_entities else 0
    print(f"Ingested {file_path.name}")
    print(f"  Stage:      {job.current_stage.value}")
    print(f"  Categories: {', '.join(job.categories) or '(none)'}")
    print(f"  Entries:    {total}")
    print(f"  Files:      {len(job.data_lake_paths)}")

    return 0 if job.current_stage == PipelineStage.INTEGRATED else 1


if __name__ == "__main__":
    raise SystemExit(main())
