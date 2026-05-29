"""Stage 3: Classify — determine document type and content categories."""

from __future__ import annotations

from typing import Any

from pipeline.models import DocumentCategory, DocumentJob, PipelineStage

# Keyword-based classification rules
CATEGORY_KEYWORDS: dict[DocumentCategory, list[str]] = {
    DocumentCategory.SIGNALS: [
        "signal", "message_id", "can", "start_bit", "dlc", "cycle_time",
        "bus", "sender", "messages",
    ],
    DocumentCategory.STATES: [
        "state", "transition", "mode", "from_state", "to_state", "guard",
        "state_machine", "gear_ranges",
    ],
    DocumentCategory.REQUIREMENTS: [
        "requirement", "req-", "shall", "priority", "verification",
        "acceptance", "rationale", "system_requirements", "verification_matrix",
        "safety_interlocks",
    ],
    DocumentCategory.DTCS: [
        "dtc", "diagnostic", "trouble_code", "mil", "fault_action",
        "debounce", "enable_condition",
    ],
    DocumentCategory.PARAMETERS: [
        "parameter", "calibration", "threshold", "tolerance", "min_value",
        "max_value", "test_condition", "calibration_parameters",
        "min value", "max value",
    ],
}


def classify_document(
    job: DocumentJob, extracted: dict[str, Any]
) -> list[DocumentCategory]:
    """Classify a document into data lake categories based on content."""
    job.advance(PipelineStage.CLASSIFYING, "Analyzing content for category classification")

    categories: list[DocumentCategory] = []
    entities = extracted.get("entities", {})
    metadata = extracted.get("metadata", {})

    # Check entity keys against category keywords
    all_keys = set()
    for key, values in entities.items():
        all_keys.add(key.lower())
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict):
                    all_keys.update(k.lower() for k in item.keys())

    # Also check metadata
    title = str(metadata.get("title", "")).lower()
    doc_id = str(metadata.get("document_id", "")).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if any(kw in k for k in all_keys))
        title_score = sum(1 for kw in keywords if kw in title or kw in doc_id)
        if score >= 1 or title_score >= 1:
            categories.append(category)

    if not categories:
        categories = [DocumentCategory.REQUIREMENTS]

    job.categories = [c.value for c in categories]
    job.advance(
        PipelineStage.CLASSIFYING,
        f"Classified into {len(categories)} categories: {', '.join(c.value for c in categories)}",
    )
    return categories
