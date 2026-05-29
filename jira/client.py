"""Jira REST API client for creating and updating issues.

In production, this connects to a real Jira instance via the REST API.
For the demo scaffold, it logs API calls and simulates responses.

Wire up real Jira by setting environment variables:
  JIRA_URL      — e.g. https://yourcompany.atlassian.net
  JIRA_EMAIL    — e.g. devin@yourcompany.com
  JIRA_TOKEN    — API token from https://id.atlassian.com/manage-profile/security/api-tokens
  JIRA_PROJECT  — e.g. AUTO
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class JiraConfig:
    """Jira connection configuration."""

    url: str
    email: str
    token: str
    project_key: str

    @classmethod
    def from_env(cls) -> JiraConfig:
        """Load config from environment variables."""
        return cls(
            url=os.environ.get("JIRA_URL", ""),
            email=os.environ.get("JIRA_EMAIL", ""),
            token=os.environ.get("JIRA_TOKEN", ""),
            project_key=os.environ.get("JIRA_PROJECT", "AUTO"),
        )

    @property
    def is_configured(self) -> bool:
        """Check if Jira is fully configured."""
        return bool(self.url and self.email and self.token)


class JiraClient:
    """Client for Jira REST API v3 operations."""

    def __init__(self, config: JiraConfig | None = None) -> None:
        self.config = config or JiraConfig.from_env()
        self._mock_log: list[dict[str, Any]] = []
        self._mock_issue_counter = 1

    @property
    def is_live(self) -> bool:
        """Whether this client is connected to a real Jira instance."""
        return self.config.is_configured

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Story",
        labels: list[str] | None = None,
        priority: str = "Medium",
    ) -> dict[str, Any]:
        """Create a Jira issue (user story, task, etc.)."""
        if self.is_live:
            return self._create_issue_live(summary, description, issue_type, labels, priority)
        return self._create_issue_mock(summary, description, issue_type, labels, priority)

    def update_issue(
        self,
        issue_key: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an existing Jira issue."""
        if self.is_live:
            return self._update_issue_live(issue_key, fields)
        return self._update_issue_mock(issue_key, fields)

    def add_comment(self, issue_key: str, body: str) -> dict[str, Any]:
        """Add a comment to an existing Jira issue."""
        if self.is_live:
            return self._add_comment_live(issue_key, body)
        return self._add_comment_mock(issue_key, body)

    def transition_issue(self, issue_key: str, transition_name: str) -> dict[str, Any]:
        """Transition an issue to a new status."""
        if self.is_live:
            return self._transition_issue_live(issue_key, transition_name)
        return self._transition_issue_mock(issue_key, transition_name)

    def get_mock_log(self) -> list[dict[str, Any]]:
        """Get the mock API call log (for demo/testing)."""
        return self._mock_log

    def save_mock_log(self, path: Path | None = None) -> None:
        """Save mock API log to a file."""
        if path is None:
            path = Path("data_lake/metadata/jira_activity.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._mock_log, indent=2))

    # --- Live Jira API calls ---

    def _create_issue_live(
        self, summary: str, description: str, issue_type: str,
        labels: list[str] | None, priority: str,
    ) -> dict[str, Any]:
        """Create issue via real Jira REST API."""
        import httpx

        payload = {
            "fields": {
                "project": {"key": self.config.project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [
                        {"type": "text", "text": description}
                    ]}],
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
            }
        }
        if labels:
            payload["fields"]["labels"] = labels

        resp = httpx.post(
            f"{self.config.url}/rest/api/3/issue",
            json=payload,
            auth=(self.config.email, self.config.token),
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    def _update_issue_live(self, issue_key: str, fields: dict[str, Any]) -> dict[str, Any]:
        import httpx

        resp = httpx.put(
            f"{self.config.url}/rest/api/3/issue/{issue_key}",
            json={"fields": fields},
            auth=(self.config.email, self.config.token),
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return {"status": "updated", "key": issue_key}

    def _add_comment_live(self, issue_key: str, body: str) -> dict[str, Any]:
        import httpx

        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": body}
                ]}],
            }
        }
        resp = httpx.post(
            f"{self.config.url}/rest/api/3/issue/{issue_key}/comment",
            json=payload,
            auth=(self.config.email, self.config.token),
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    def _transition_issue_live(self, issue_key: str, transition_name: str) -> dict[str, Any]:
        import httpx

        # First get available transitions
        resp = httpx.get(
            f"{self.config.url}/rest/api/3/issue/{issue_key}/transitions",
            auth=(self.config.email, self.config.token),
        )
        resp.raise_for_status()
        transitions = resp.json().get("transitions", [])
        target = next(
            (t for t in transitions if t["name"].lower() == transition_name.lower()),
            None,
        )
        if not target:
            return {"error": f"Transition '{transition_name}' not found"}

        resp = httpx.post(
            f"{self.config.url}/rest/api/3/issue/{issue_key}/transitions",
            json={"transition": {"id": target["id"]}},
            auth=(self.config.email, self.config.token),
        )
        resp.raise_for_status()
        return {"status": "transitioned", "key": issue_key, "to": transition_name}

    # --- Mock implementations ---

    def _create_issue_mock(
        self, summary: str, description: str, issue_type: str,
        labels: list[str] | None, priority: str,
    ) -> dict[str, Any]:
        key = f"{self.config.project_key}-{self._mock_issue_counter}"
        self._mock_issue_counter += 1
        result = {
            "key": key,
            "self": f"{self.config.url or 'https://mock.atlassian.net'}/rest/api/3/issue/{key}",
            "fields": {
                "summary": summary,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
                "labels": labels or [],
                "status": {"name": "To Do"},
            },
        }
        self._mock_log.append({
            "action": "create_issue",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": {"summary": summary, "issue_type": issue_type, "labels": labels},
            "response": result,
        })
        return result

    def _update_issue_mock(self, issue_key: str, fields: dict[str, Any]) -> dict[str, Any]:
        result = {"status": "updated", "key": issue_key}
        self._mock_log.append({
            "action": "update_issue",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": {"issue_key": issue_key, "fields": fields},
            "response": result,
        })
        return result

    def _add_comment_mock(self, issue_key: str, body: str) -> dict[str, Any]:
        result = {"id": "10001", "key": issue_key, "body": body}
        self._mock_log.append({
            "action": "add_comment",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": {"issue_key": issue_key, "body": body[:200]},
            "response": result,
        })
        return result

    def _transition_issue_mock(self, issue_key: str, transition_name: str) -> dict[str, Any]:
        result = {"status": "transitioned", "key": issue_key, "to": transition_name}
        self._mock_log.append({
            "action": "transition_issue",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": {"issue_key": issue_key, "transition": transition_name},
            "response": result,
        })
        return result
