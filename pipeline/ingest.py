"""Stage 1: Ingest — receive file and extract metadata."""

from __future__ import annotations

import uuid
from pathlib import Path

from pipeline.models import DocumentJob, PipelineStage


def ingest_file(file_path: Path) -> DocumentJob:
    """Receive a file and create a processing job with metadata."""
    job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
    suffix = file_path.suffix.lower()

    file_type_map = {
        ".json": "extracted_json",
        ".md": "markdown_spec",
        ".xlsx": "excel_workbook",
        ".pdf": "pdf_document",
        ".docx": "word_document",
    }
    file_type = file_type_map.get(suffix, "unknown")

    job = DocumentJob(
        job_id=job_id,
        filename=file_path.name,
        file_size=file_path.stat().st_size if file_path.exists() else 0,
        file_type=file_type,
    )
    job.advance(
        PipelineStage.RECEIVED,
        f"File received: {file_path.name} ({job.file_size:,} bytes, type: {file_type})",
    )
    return job
