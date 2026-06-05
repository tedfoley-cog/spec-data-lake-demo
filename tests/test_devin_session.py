"""Tests for the Devin-session ingestion wiring (no network calls)."""

from __future__ import annotations

import pytest

from pipeline import devin_session, repo_ingest


def test_slugify_and_branch_name() -> None:
    assert repo_ingest.slugify("EPS Control Module Spec.pdf") == "eps-control-module-spec"
    branch = repo_ingest.make_branch_name("My File!.pdf")
    assert branch.startswith("ingest/my-file-")
    assert branch.rsplit("-", 1)[1].isdigit()


def test_build_ingest_prompt_contains_key_instructions() -> None:
    prompt = devin_session.build_ingest_prompt(
        "spec.pdf", "ingest/spec-123", "source_documents/dropped/spec.pdf", "owner/repo"
    )
    assert "ingest/spec-123" in prompt
    assert "source_documents/dropped/spec.pdf" in prompt
    assert "python -m pipeline.cli" in prompt
    assert "owner/repo" in prompt


def test_sessions_enabled_requires_token_and_org(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEVIN_API_TOKEN", raising=False)
    monkeypatch.delenv("TEDDY_SERVICE_USER_TOKEN", raising=False)
    monkeypatch.delenv("DEVIN_ORG_ID", raising=False)
    monkeypatch.delenv("TEDDY_ORG_ID", raising=False)
    assert devin_session.sessions_enabled() is False

    monkeypatch.setenv("DEVIN_API_TOKEN", "tok")
    assert devin_session.sessions_enabled() is False  # org still missing

    monkeypatch.setenv("DEVIN_ORG_ID", "org-x")
    assert devin_session.sessions_enabled() is True


def test_git_enabled_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEDFOLEY_COG_REPO_PAT", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert repo_ingest.git_enabled() is False
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    assert repo_ingest.git_enabled() is True


def test_create_session_without_config_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEVIN_API_TOKEN", raising=False)
    monkeypatch.delenv("TEDDY_SERVICE_USER_TOKEN", raising=False)
    monkeypatch.delenv("DEVIN_ORG_ID", raising=False)
    monkeypatch.delenv("TEDDY_ORG_ID", raising=False)
    with pytest.raises(EnvironmentError):
        devin_session.create_ingest_session("spec.pdf", "ingest/x", "p/spec.pdf")
