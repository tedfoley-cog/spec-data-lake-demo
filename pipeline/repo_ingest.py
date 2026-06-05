"""GitHub helpers for the authentic ingestion flow.

Uses the GitHub REST contents API (with a fine-grained PAT) to:

* create a fresh ``ingest/<doc>-<ts>`` branch and commit the dropped file to it
  *without* touching the dashboard's own working tree, and
* read back the ``data_lake/<category>/*.json`` entries a Devin ingestion session
  commits to that branch, so the dashboard can reflect them.

Authentication uses ``TEDFOLEY_COG_REPO_PAT`` (falling back to ``GITHUB_TOKEN``).
When no token is configured the dashboard falls back to in-process processing.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from typing import Any

import httpx

GITHUB_API = "https://api.github.com"
DEFAULT_REPO = os.environ.get("SPEC_DATA_LAKE_REPO", "tedfoley-cog/spec-data-lake-demo")
DROP_DIR = "source_documents/dropped"


def default_base() -> str:
    """Branch to cut ingest branches from (and target PRs at).

    Defaults to ``main``. Set ``INGEST_BASE_BRANCH`` to branch off a branch that
    has the latest pipeline (e.g. before this work is merged to ``main``), so
    spawned sessions clone the pipeline + CLI they need to ingest the document.
    """
    return os.environ.get("INGEST_BASE_BRANCH", "main")


def github_token() -> str | None:
    """Return the configured GitHub token, if any."""
    return os.environ.get("TEDFOLEY_COG_REPO_PAT") or os.environ.get("GITHUB_TOKEN")


def git_enabled() -> bool:
    """True when a GitHub token is available to push branches."""
    return bool(github_token())


def _client() -> httpx.Client:
    token = github_token()
    if not token:
        raise EnvironmentError(
            "No GitHub token (set TEDFOLEY_COG_REPO_PAT or GITHUB_TOKEN)."
        )
    return httpx.Client(
        base_url=GITHUB_API,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30.0,
    )


def slugify(name: str) -> str:
    """Turn a filename into a branch-safe slug."""
    stem = re.sub(r"\.[^.]+$", "", name)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
    return slug or "document"


def make_branch_name(filename: str) -> str:
    """Build a unique ``ingest/<slug>-<ts>`` branch name."""
    return f"ingest/{slugify(filename)}-{int(time.time())}"


def push_dropped_file(
    filename: str,
    content: bytes,
    branch: str,
    repo: str | None = None,
    base: str | None = None,
) -> dict[str, Any]:
    """Create ``branch`` off ``base`` and commit the dropped file to it."""
    repo = repo or DEFAULT_REPO
    base = base or default_base()
    dest_path = f"{DROP_DIR}/{filename}"
    with _client() as client:
        ref = client.get(f"/repos/{repo}/git/ref/heads/{base}")
        ref.raise_for_status()
        base_sha = ref.json()["object"]["sha"]

        created = client.post(
            f"/repos/{repo}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": base_sha},
        )
        # 422 == branch already exists; anything else unexpected is an error.
        if created.status_code not in (201, 422):
            created.raise_for_status()

        put = client.put(
            f"/repos/{repo}/contents/{dest_path}",
            json={
                "message": f"Drop {filename} for ingestion",
                "content": base64.b64encode(content).decode("ascii"),
                "branch": branch,
            },
        )
        put.raise_for_status()
    return {"branch": branch, "path": dest_path, "repo": repo}


def read_data_lake_from_branch(
    branch: str,
    repo: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Read committed ``data_lake/<category>/*.json`` files from ``branch``.

    Returns ``{category: [file_payload, ...]}``. Empty when nothing committed yet.
    """
    repo = repo or DEFAULT_REPO
    out: dict[str, list[dict[str, Any]]] = {}
    with _client() as client:
        top = client.get(
            f"/repos/{repo}/contents/data_lake", params={"ref": branch}
        )
        if top.status_code == 404:
            return out
        top.raise_for_status()
        for cat in top.json():
            if cat.get("type") != "dir" or cat["name"] == "metadata":
                continue
            listing = client.get(
                f"/repos/{repo}/contents/data_lake/{cat['name']}",
                params={"ref": branch},
            )
            if listing.status_code != 200:
                continue
            files: list[dict[str, Any]] = []
            for entry in listing.json():
                if entry.get("type") != "file" or not entry["name"].endswith(".json"):
                    continue
                blob = client.get(
                    f"/repos/{repo}/contents/{entry['path']}",
                    params={"ref": branch},
                )
                if blob.status_code != 200:
                    continue
                payload = blob.json()
                try:
                    decoded = base64.b64decode(payload["content"]).decode("utf-8")
                    files.append(json.loads(decoded))
                except (KeyError, ValueError):
                    continue
            if files:
                out[cat["name"]] = files
    return out
