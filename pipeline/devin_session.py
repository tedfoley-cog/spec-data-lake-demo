"""Create real Devin sessions that ingest dropped documents into the data lake.

The dashboard's *authentic* ingestion flow does not process files in-process.
Dropping a file commits it to a fresh ``ingest/<doc>-<ts>`` branch and launches a
real Devin session (via the Devin v3 REST API). That session runs the 6-stage
pipeline and commits the structured ``data_lake/`` entries back to the branch;
the dashboard then reflects those committed entries.

Authentication uses ``DEVIN_API_TOKEN`` (falling back to
``TEDDY_SERVICE_USER_TOKEN``). When no token is configured the dashboard runs the
pipeline in-process instead, so the app still works offline.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# Always use the v3 API — v1 paths are outdated. v3 session routes are
# organization-scoped: /v3/organizations/{org_id}/sessions[/{devin_id}].
DEVIN_API_BASE = "https://api.devin.ai/v3"
DEFAULT_REPO = os.environ.get("SPEC_DATA_LAKE_REPO", "tedfoley-cog/spec-data-lake-demo")


def devin_token() -> str | None:
    """Return the configured Devin API token, if any."""
    return os.environ.get("DEVIN_API_TOKEN") or os.environ.get("TEDDY_SERVICE_USER_TOKEN")


def org_id() -> str | None:
    """Return the configured Devin organization ID, if any."""
    return os.environ.get("DEVIN_ORG_ID") or os.environ.get("TEDDY_ORG_ID")


def sessions_enabled() -> bool:
    """True when a Devin API token and org ID are available to create sessions."""
    return bool(devin_token() and org_id())


def build_ingest_prompt(
    filename: str, branch: str, file_path: str, repo: str, base: str = "main"
) -> str:
    """Build the prompt instructing a session to ingest one dropped document."""
    return (
        f"A new automotive engineering specification `{filename}` was just dropped into "
        f"the Spec Data Lake dashboard. It is already committed to the branch `{branch}` "
        f"of `{repo}` at `{file_path}`.\n\n"
        f"Ingest it into the structured data lake by doing EXACTLY this:\n\n"
        f"1. Clone `https://github.com/{repo}` and check out the existing branch "
        f"`{branch}` (do not create a new branch).\n"
        f"2. Install dependencies with `uv sync`.\n"
        f"3. Run the 6-stage ingestion pipeline on the dropped file from the repo root:\n"
        f'   `uv run python -m pipeline.cli "{file_path}"`\n'
        f"   This extracts, classifies, structures, validates and integrates the spec, "
        f"writing JSON entries into `data_lake/<category>/` and updating "
        f"`dashboard/state.json`.\n"
        f"4. Stage and commit ONLY the generated `data_lake/` files and "
        f"`dashboard/state.json` (commit message: `Ingest {filename} into data lake`) "
        f"and push to `{branch}`.\n"
        f"5. Open a pull request from `{branch}` into `{base}` titled "
        f"`Ingest {filename} into data lake`.\n\n"
        f"Do not modify any pipeline source code — keep the changes limited to the "
        f"data-lake outputs the pipeline produces."
    )


def create_ingest_session(
    filename: str,
    branch: str,
    file_path: str,
    repo: str | None = None,
    base: str = "main",
) -> dict[str, Any]:
    """Create a Devin session to ingest ``file_path`` on ``branch``.

    Returns the raw API response (contains ``session_id`` and ``url``).
    """
    token = devin_token()
    org = org_id()
    if not token or not org:
        raise EnvironmentError(
            "Devin API not configured (need DEVIN_API_TOKEN/TEDDY_SERVICE_USER_TOKEN "
            "and DEVIN_ORG_ID/TEDDY_ORG_ID)."
        )
    repo = repo or DEFAULT_REPO
    payload: dict[str, Any] = {
        "prompt": build_ingest_prompt(filename, branch, file_path, repo, base),
        "title": f"Ingest {filename} into data lake",
        "tags": ["spec-data-lake", "ingestion"],
    }
    with httpx.Client(
        base_url=DEVIN_API_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    ) as client:
        resp = client.post(f"/organizations/{org}/sessions", json=payload)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    return data


def get_session_status(session_id: str) -> dict[str, Any]:
    """Fetch live status via ``GET /v3/organizations/{org_id}/sessions/{id}``."""
    token = devin_token()
    org = org_id()
    if not token or not org:
        raise EnvironmentError("Devin API not configured.")
    with httpx.Client(
        base_url=DEVIN_API_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    ) as client:
        resp = client.get(f"/organizations/{org}/sessions/{session_id}")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    return data
