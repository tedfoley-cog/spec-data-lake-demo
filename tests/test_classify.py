"""Tests for document classification."""

from __future__ import annotations

from pipeline.classify import classify_document
from pipeline.models import DocumentCategory, DocumentJob


def _make_job() -> DocumentJob:
    return DocumentJob(job_id="TEST-001", filename="test.json", file_type="extracted_json")


class TestClassifyDocument:
    def test_signals_classification(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "messages": [
                    {"message_id": "0x100", "signals": [{"name": "RPM", "start_bit": 0}]},
                ],
            },
            "metadata": {"title": "CAN Signal Catalog"},
        }
        categories = classify_document(job, extracted)
        assert DocumentCategory.SIGNALS in categories

    def test_states_classification(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "states": [{"state_id": "S1"}],
                "transitions": [{"from_state": "S1", "to_state": "S2"}],
            },
            "metadata": {"title": "State Machine Spec"},
        }
        categories = classify_document(job, extracted)
        assert DocumentCategory.STATES in categories

    def test_dtcs_classification(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "dtcs": [{"code": "P0335", "diagnostic": True, "mil": True}],
            },
            "metadata": {"title": "Diagnostic Trouble Code Matrix"},
        }
        categories = classify_document(job, extracted)
        assert DocumentCategory.DTCS in categories

    def test_empty_defaults_to_requirements(self) -> None:
        job = _make_job()
        extracted = {"entities": {}, "metadata": {}}
        categories = classify_document(job, extracted)
        assert DocumentCategory.REQUIREMENTS in categories
