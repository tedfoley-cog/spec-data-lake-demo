"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_source_dir(tmp_path: Path) -> Path:
    """Create a temporary source directory with a sample extracted JSON."""
    source_dir = tmp_path / "source_documents"
    source_dir.mkdir()

    sample = {
        "document_id": "TEST-001",
        "title": "Test Document",
        "revision": "A",
        "subsystem": "Test",
        "asil": "QM",
        "effective_date": "2024-01-01",
        "states": [
            {"state_id": "S1", "code": "0x01", "name": "State One", "description": "First state"},
            {"state_id": "S2", "code": "0x02", "name": "State Two", "description": "Second state"},
        ],
        "transitions": [
            {"from_state": "S1", "to_state": "S2", "condition": "EVENT_A", "category": "forward"},
        ],
        "dtcs": [
            {"code": "P0001", "description": "Test DTC", "category": "test",
             "enable_condition": "Always", "fault_action": "Log", "mil": True},
        ],
        "diagrams": [],
        "tables": 2,
    }
    (source_dir / "test_spec.extracted.json").write_text(json.dumps(sample))
    return source_dir


@pytest.fixture
def tmp_data_lake(tmp_path: Path) -> Path:
    """Create a temporary data lake directory."""
    dl = tmp_path / "data_lake"
    for sub in ["signals", "states", "requirements", "dtcs", "parameters",
                "relationships", "metadata"]:
        (dl / sub).mkdir(parents=True)
    return dl


@pytest.fixture(autouse=True)
def _change_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Change working directory to tmp_path for each test."""
    monkeypatch.chdir(tmp_path)
    for sub in ["data_lake/signals", "data_lake/states", "data_lake/requirements",
                "data_lake/dtcs", "data_lake/parameters", "data_lake/relationships",
                "data_lake/metadata", "dashboard"]:
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
