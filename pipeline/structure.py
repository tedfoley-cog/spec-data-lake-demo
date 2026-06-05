"""Stage 4: Structure — convert extracted data to data lake schema."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from pipeline.models import (
    DataLakeEntry,
    DocumentCategory,
    DocumentJob,
    PipelineStage,
)


def structure_for_data_lake(
    job: DocumentJob,
    extracted: dict[str, Any],
    categories: list[DocumentCategory],
) -> list[DataLakeEntry]:
    """Convert extracted entities into structured data lake entries."""
    job.advance(PipelineStage.STRUCTURING, "Converting to data lake schema")

    entries: list[DataLakeEntry] = []
    entities = extracted.get("entities", {})
    metadata = extracted.get("metadata", {})
    doc_id = str(metadata.get("document_id", job.filename))
    revision = str(metadata.get("revision", "1"))

    for category in categories:
        category_entries = _structure_category(category, entities, doc_id, revision)
        entries.extend(category_entries)

    entity_counts: dict[str, int] = {}
    for entry in entries:
        cat = entry.category.value
        entity_counts[cat] = entity_counts.get(cat, 0) + 1
    job.extracted_entities = entity_counts

    job.advance(
        PipelineStage.STRUCTURING,
        f"Structured {len(entries)} entries across {len(categories)} categories",
    )
    return entries


def _sanitize_id_part(text: str) -> str:
    """Normalize a free-text fragment into an entry_id-safe token."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper()


def _structure_category(
    category: DocumentCategory,
    entities: dict[str, Any],
    doc_id: str,
    revision: str,
) -> list[DataLakeEntry]:
    """Structure entities for a specific data lake category."""
    entries: list[DataLakeEntry] = []

    if category == DocumentCategory.SIGNALS:
        entries.extend(_structure_signals(entities, doc_id, revision))
    elif category == DocumentCategory.STATES:
        entries.extend(_structure_states(entities, doc_id, revision))
    elif category == DocumentCategory.REQUIREMENTS:
        entries.extend(_structure_requirements(entities, doc_id, revision))
    elif category == DocumentCategory.DTCS:
        entries.extend(_structure_dtcs(entities, doc_id, revision))
    elif category == DocumentCategory.PARAMETERS:
        entries.extend(_structure_parameters(entities, doc_id, revision))

    return entries


def _structure_signals(
    entities: dict[str, Any], doc_id: str, revision: str
) -> list[DataLakeEntry]:
    """Structure CAN signal entries."""
    entries: list[DataLakeEntry] = []

    # From messages array (CAN signal catalog format)
    for msg in entities.get("messages", []):
        if not isinstance(msg, dict):
            continue
        msg_id = msg.get("message_id", msg.get("name", ""))
        for sig in msg.get("signals", []):
            if not isinstance(sig, dict):
                continue
            entry_id = f"SIG-{msg_id}-{sig.get('name', '')}"
            entries.append(DataLakeEntry(
                entry_id=entry_id,
                category=DocumentCategory.SIGNALS,
                source_document=doc_id,
                source_revision=revision,
                data={
                    "signal_name": sig.get("name", ""),
                    "message_id": msg_id,
                    "message_name": msg.get("name", ""),
                    "start_bit": sig.get("start_bit", 0),
                    "length": sig.get("length", 0),
                    "scale": sig.get("scale", 1),
                    "offset": sig.get("offset", 0),
                    "unit": sig.get("unit", ""),
                    "bus": msg.get("bus", "HS-CAN"),
                    "cycle_time_ms": msg.get("cycle_time_ms", 0),
                },
            ))

    # From input_signals / output_signals arrays
    for key in ["input_signals", "output_signals"]:
        for sig in entities.get(key, []):
            if not isinstance(sig, dict):
                continue
            entry_id = f"SIG-{sig.get('message_id', '')}-{sig.get('name', '')}"
            entries.append(DataLakeEntry(
                entry_id=entry_id,
                category=DocumentCategory.SIGNALS,
                source_document=doc_id,
                source_revision=revision,
                data={
                    "signal_name": sig.get("name", ""),
                    "message_id": sig.get("message_id", ""),
                    "direction": "input" if key == "input_signals" else "output",
                    "bit_position": sig.get("bit_position", 0),
                    "length": sig.get("length", 0),
                    "scale": sig.get("scale", 1),
                    "unit": sig.get("unit", ""),
                },
            ))

    # From flat signals arrays (transmission format)
    for sig in entities.get("signals", []):
        if not isinstance(sig, dict):
            continue
        entry_id = f"SIG-{sig.get('message_id', '')}-{sig.get('name', '')}"
        entries.append(DataLakeEntry(
            entry_id=entry_id,
            category=DocumentCategory.SIGNALS,
            source_document=doc_id,
            source_revision=revision,
            data=sig,
        ))

    return entries


def _structure_states(
    entities: dict[str, Any], doc_id: str, revision: str
) -> list[DataLakeEntry]:
    """Structure state machine entries."""
    entries: list[DataLakeEntry] = []

    for state in entities.get("states", []):
        if not isinstance(state, dict):
            continue
        entry_id = f"STATE-{state.get('state_id', state.get('name', ''))}"
        entries.append(DataLakeEntry(
            entry_id=entry_id,
            category=DocumentCategory.STATES,
            source_document=doc_id,
            source_revision=revision,
            data=state,
        ))

    # Count from/to pairs so multiple transitions between the same states
    # (e.g. several RUN_ENGINE->EMERGENCY conditions) get unique entry_ids.
    pair_counts = Counter(
        (t.get("from_state", ""), t.get("to_state", ""))
        for t in entities.get("transitions", [])
        if isinstance(t, dict)
    )
    for trans in entities.get("transitions", []):
        if not isinstance(trans, dict):
            continue
        from_s = trans.get("from_state", "")
        to_s = trans.get("to_state", "")
        entry_id = f"TRANS-{from_s}-{to_s}"
        if pair_counts[(from_s, to_s)] > 1:
            cond = _sanitize_id_part(str(trans.get("condition", "")))
            if cond:
                entry_id = f"{entry_id}-{cond}"
        entries.append(DataLakeEntry(
            entry_id=entry_id,
            category=DocumentCategory.STATES,
            source_document=doc_id,
            source_revision=revision,
            data=trans,
        ))

    for gr in entities.get("gear_ranges", []):
        if not isinstance(gr, dict):
            continue
        entry_id = f"GEAR-{gr.get('range', '')}"
        entries.append(DataLakeEntry(
            entry_id=entry_id,
            category=DocumentCategory.STATES,
            source_document=doc_id,
            source_revision=revision,
            data=gr,
        ))

    return entries


def _structure_requirements(
    entities: dict[str, Any], doc_id: str, revision: str
) -> list[DataLakeEntry]:
    """Structure requirement entries."""
    entries: list[DataLakeEntry] = []

    for key in ["requirements", "safety_interlocks", "system_requirements",
                 "verification_matrix"]:
        for req in entities.get(key, []):
            if not isinstance(req, dict):
                continue
            req_id = req.get("Requirement ID", req.get("requirement_id",
                    req.get("shift", f"REQ-{len(entries)+1}")))
            entry_id = f"REQ-{req_id}"
            entries.append(DataLakeEntry(
                entry_id=entry_id,
                category=DocumentCategory.REQUIREMENTS,
                source_document=doc_id,
                source_revision=revision,
                data=req,
            ))

    return entries


def _structure_dtcs(
    entities: dict[str, Any], doc_id: str, revision: str
) -> list[DataLakeEntry]:
    """Structure diagnostic trouble code entries."""
    entries: list[DataLakeEntry] = []

    for dtc in entities.get("dtcs", []):
        if not isinstance(dtc, dict):
            continue
        entry_id = f"DTC-{dtc.get('code', '')}"
        entries.append(DataLakeEntry(
            entry_id=entry_id,
            category=DocumentCategory.DTCS,
            source_document=doc_id,
            source_revision=revision,
            data=dtc,
        ))

    return entries


def _structure_parameters(
    entities: dict[str, Any], doc_id: str, revision: str
) -> list[DataLakeEntry]:
    """Structure calibration parameter entries."""
    entries: list[DataLakeEntry] = []

    for key in ["parameters", "timing_constraints", "calibration_parameters"]:
        params = entities.get(key, {})
        if isinstance(params, dict):
            for param_name, param_value in params.items():
                entry_id = f"PARAM-{param_name}"
                entries.append(DataLakeEntry(
                    entry_id=entry_id,
                    category=DocumentCategory.PARAMETERS,
                    source_document=doc_id,
                    source_revision=revision,
                    data={"name": param_name, "value": param_value},
                ))
        elif isinstance(params, list):
            for param in params:
                if not isinstance(param, dict):
                    continue
                param_name = param.get("Parameter ID", param.get("Name",
                    param.get("name", param.get("parameter", f"P{len(entries)+1}"))))
                entry_id = f"PARAM-{param_name}"
                entries.append(DataLakeEntry(
                    entry_id=entry_id,
                    category=DocumentCategory.PARAMETERS,
                    source_document=doc_id,
                    source_revision=revision,
                    data=param,
                ))

    return entries
