"""Create Jira user stories from pipeline findings."""

from __future__ import annotations

from typing import Any

from jira.client import JiraClient
from pipeline.models import DataLakeEntry, DocumentCategory, DocumentJob


def create_stories_from_pipeline(
    job: DocumentJob,
    entries: list[DataLakeEntry],
    jira: JiraClient | None = None,
) -> list[dict[str, Any]]:
    """Create Jira user stories for entities discovered during pipeline processing.

    Groups entries by category and creates one user story per category with
    details of all extracted entities.
    """
    if jira is None:
        jira = JiraClient()

    stories: list[dict[str, Any]] = []
    by_category: dict[str, list[DataLakeEntry]] = {}
    for entry in entries:
        cat = entry.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(entry)

    for category, cat_entries in by_category.items():
        summary = _build_summary(category, cat_entries, job)
        description = _build_description(category, cat_entries, job)
        labels = ["data-lake", f"category-{category}", "auto-generated"]

        result = jira.create_issue(
            summary=summary,
            description=description,
            issue_type="Story",
            labels=labels,
            priority="Medium",
        )
        stories.append(result)

    return stories


def update_trigger_issue(
    trigger_issue_key: str,
    jobs: list[DocumentJob],
    jira: JiraClient | None = None,
) -> dict[str, Any]:
    """Update the triggering Jira issue with processing results and close it."""
    if jira is None:
        jira = JiraClient()

    total_entries = sum(
        sum(job.extracted_entities.values()) for job in jobs
    )
    total_categories = set()
    for job in jobs:
        total_categories.update(job.categories)

    comment = (
        f"Data lake ingestion complete.\n\n"
        f"Documents processed: {len(jobs)}\n"
        f"Total entities extracted: {total_entries}\n"
        f"Categories populated: {', '.join(sorted(total_categories))}\n\n"
        f"User stories created for each category. "
        f"Data lake is updated and ready for consumption."
    )

    jira.add_comment(trigger_issue_key, comment)
    jira.transition_issue(trigger_issue_key, "Done")

    return {"issue_key": trigger_issue_key, "status": "closed", "comment": comment}


def _build_summary(
    category: str, entries: list[DataLakeEntry], job: DocumentJob
) -> str:
    """Build a user story summary."""
    category_titles = {
        DocumentCategory.SIGNALS.value: "CAN Signal Definitions",
        DocumentCategory.STATES.value: "State Machine Definitions",
        DocumentCategory.REQUIREMENTS.value: "Requirements",
        DocumentCategory.DTCS.value: "Diagnostic Trouble Codes",
        DocumentCategory.PARAMETERS.value: "Calibration Parameters",
        DocumentCategory.RELATIONSHIPS.value: "Cross-Document Relationships",
    }
    title = category_titles.get(category, category.title())
    return f"Data Lake Update: {len(entries)} {title} from {job.filename}"


def _build_description(
    category: str, entries: list[DataLakeEntry], job: DocumentJob
) -> str:
    """Build a user story description with entity details."""
    lines = [
        f"Source: {job.filename} (Job {job.job_id})",
        f"Category: {category}",
        f"Entries: {len(entries)}",
        "",
        "Extracted entities:",
    ]
    for entry in entries[:10]:
        lines.append(f"  - {entry.entry_id}: {_summarize_entry(entry)}")
    if len(entries) > 10:
        lines.append(f"  ... and {len(entries) - 10} more")

    return "\n".join(lines)


def _summarize_entry(entry: DataLakeEntry) -> str:
    """One-line summary of an entry's data."""
    data = entry.data
    if "signal_name" in data:
        return f"{data['signal_name']} (msg {data.get('message_id', '?')})"
    if "name" in data:
        return str(data["name"])
    if "state_id" in data:
        return f"State {data['state_id']}: {data.get('description', '')}"
    if "code" in data:
        return f"{data['code']}: {data.get('description', '')}"
    if "from_state" in data:
        return f"{data['from_state']} -> {data['to_state']}"
    if "shift" in data:
        return f"Interlock: {data['shift']}"
    return str(list(data.keys())[:3])
