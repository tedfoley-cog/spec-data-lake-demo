"""Jira webhook handler — receives events and triggers pipeline processing.

Registers FastAPI routes for:
  POST /jira/webhook — receive Jira webhook events
  GET  /jira/activity — view Jira activity log
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/jira", tags=["jira"])

ACTIVITY_LOG = Path("data_lake/metadata/jira_activity.json")


@router.post("/webhook")
async def jira_webhook(request: Request) -> JSONResponse:
    """Handle incoming Jira webhook events.

    When a Jira issue is created or updated with the 'data-lake-ingest' label,
    triggers the document processing pipeline.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    event_type = payload.get("webhookEvent", "")
    issue = payload.get("issue", {})
    issue_key = issue.get("key", "")
    labels = [
        lbl.get("name", "") if isinstance(lbl, dict) else str(lbl)
        for lbl in issue.get("fields", {}).get("labels", [])
    ]

    result: dict[str, Any] = {
        "received": True,
        "event_type": event_type,
        "issue_key": issue_key,
    }

    if "data-lake-ingest" in labels:
        result["action"] = "pipeline_triggered"
        result["message"] = (
            f"Pipeline triggered for {issue_key}. "
            f"Devin will process attached documents and update the data lake."
        )

        # Log the webhook event
        _log_activity({
            "type": "webhook_received",
            "event": event_type,
            "issue_key": issue_key,
            "action": "pipeline_triggered",
        })

        # In a real deployment, this would trigger a Devin session via the API:
        # POST https://api.devin.ai/v3/sessions
        # with prompt: "Process documents from Jira issue {issue_key}
        #               and update the data lake"
    else:
        result["action"] = "ignored"
        result["message"] = "Issue does not have 'data-lake-ingest' label"

    return JSONResponse(result)


@router.get("/activity")
def jira_activity() -> Any:
    """Get the Jira activity log."""
    if not ACTIVITY_LOG.exists():
        return {"activity": [], "count": 0}
    with open(ACTIVITY_LOG) as f:
        activity = json.load(f)
    if isinstance(activity, list):
        return {"activity": activity, "count": len(activity)}
    return activity


def _log_activity(entry: dict[str, Any]) -> None:
    """Append an entry to the activity log."""
    ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    activity: list[dict[str, Any]] = []
    if ACTIVITY_LOG.exists():
        with open(ACTIVITY_LOG) as f:
            data = json.load(f)
        if isinstance(data, list):
            activity = data
    activity.append(entry)
    ACTIVITY_LOG.write_text(json.dumps(activity, indent=2))
