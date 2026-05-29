"""Stage 2: Extract — identify text, tables, diagram regions, and structured data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.models import DocumentJob, PipelineStage


def extract_content(job: DocumentJob, file_path: Path) -> dict[str, Any]:
    """Extract structured content from a document file.

    For pre-extracted JSON files, loads them directly.
    For markdown files, identifies sections and embedded references.
    For Excel files, reads sheet structure.
    """
    job.advance(PipelineStage.EXTRACTING, f"Extracting content from {job.filename}")

    extracted: dict[str, Any] = {"raw_sections": [], "tables": 0, "diagrams": [], "entities": {}}

    if job.file_type == "extracted_json":
        extracted = _extract_from_json(file_path)
    elif job.file_type == "markdown_spec":
        extracted = _extract_from_markdown(file_path)
    elif job.file_type == "excel_workbook":
        extracted = _extract_from_excel(file_path)
    else:
        extracted["raw_sections"] = [{"type": "unknown", "content": "Unsupported file type"}]

    entity_count = sum(
        len(v) if isinstance(v, list) else 1
        for v in extracted.get("entities", {}).values()
    )
    job.advance(
        PipelineStage.EXTRACTING,
        f"Extracted {entity_count} entities, {extracted.get('tables', 0)} tables, "
        f"{len(extracted.get('diagrams', []))} diagrams",
    )
    return extracted


def _extract_from_json(file_path: Path) -> dict[str, Any]:
    """Extract from pre-extracted JSON files."""
    with open(file_path) as f:
        data = json.load(f)

    entities: dict[str, list[Any]] = {}
    diagrams: list[str] = data.get("diagrams", [])
    tables = data.get("tables", 0)

    # Collect all entity arrays from the JSON
    for key in ["states", "transitions", "signals", "dtcs", "input_signals",
                 "output_signals", "gear_ranges", "safety_interlocks",
                 "messages", "upshift_schedule"]:
        if key in data:
            val = data[key]
            if isinstance(val, list):
                entities[key] = val
            elif isinstance(val, dict) and "shifts" in val:
                entities[key] = val["shifts"]

    return {
        "raw_sections": [],
        "tables": tables,
        "diagrams": diagrams,
        "entities": entities,
        "metadata": {
            k: data[k]
            for k in ["document_id", "title", "revision", "subsystem", "asil",
                       "effective_date"]
            if k in data
        },
    }


def _extract_from_markdown(file_path: Path) -> dict[str, Any]:
    """Extract structure from markdown spec files."""
    content = file_path.read_text()
    sections: list[dict[str, str]] = []
    diagrams: list[str] = []
    table_count = 0

    current_section = ""
    for line in content.split("\n"):
        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            sections.append({"heading": current_section, "type": "section"})
        elif "![" in line:
            # Image reference
            start = line.find("(") + 1
            end = line.find(")")
            if start > 0 and end > start:
                diagrams.append(line[start:end])
        elif line.startswith("|") and "---" not in line:
            table_count += 1

    return {
        "raw_sections": sections,
        "tables": max(1, table_count // 3),
        "diagrams": diagrams,
        "entities": {},
    }


def _extract_from_excel(file_path: Path) -> dict[str, Any]:
    """Extract from Excel workbooks."""
    try:
        from openpyxl import load_workbook

        wb = load_workbook(str(file_path), read_only=True, data_only=True)
        entities: dict[str, list[dict[str, Any]]] = {}
        table_count = 0

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue

            headers = [str(h or "").strip() for h in rows[0]]
            records: list[dict[str, Any]] = []
            for row in rows[1:]:
                record = {}
                for i, val in enumerate(row):
                    if i < len(headers) and headers[i]:
                        record[headers[i]] = val
                if any(v is not None for v in record.values()):
                    records.append(record)
            if records:
                entities[sheet_name.lower().replace(" ", "_")] = records
                table_count += 1

        wb.close()
        return {
            "raw_sections": [{"type": "sheet", "heading": s} for s in wb.sheetnames],
            "tables": table_count,
            "diagrams": [],
            "entities": entities,
        }
    except Exception:
        return {"raw_sections": [], "tables": 0, "diagrams": [], "entities": {}}
