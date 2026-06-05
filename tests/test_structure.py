"""Tests for data lake structuring."""

from __future__ import annotations

from pipeline.models import DocumentCategory, DocumentJob
from pipeline.structure import structure_for_data_lake


def _make_job() -> DocumentJob:
    return DocumentJob(job_id="TEST-001", filename="test.json")


class TestStructureSignals:
    def test_structures_can_messages(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "messages": [
                    {
                        "message_id": "0x120",
                        "name": "PCM_Engine",
                        "bus": "HS-CAN",
                        "cycle_time_ms": 10,
                        "signals": [
                            {"name": "RPM", "start_bit": 0,
                             "length": 16, "scale": 0.25, "unit": "rpm"},
                            {"name": "Torque", "start_bit": 16,
                             "length": 16, "scale": 0.1, "unit": "Nm"},
                        ],
                    },
                ],
            },
            "metadata": {"document_id": "ES-CAN-001", "revision": "A"},
        }
        entries = structure_for_data_lake(job, extracted, [DocumentCategory.SIGNALS])
        assert len(entries) == 2
        assert all(e.category == DocumentCategory.SIGNALS for e in entries)
        assert entries[0].data["signal_name"] == "RPM"

    def test_structures_io_signals(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "input_signals": [
                    {"name": "IGN_SW", "message_id": "0x510", "bit_position": 0, "length": 3,
                     "scale": 1, "unit": "enum"},
                ],
            },
            "metadata": {"document_id": "ES-001", "revision": "A"},
        }
        entries = structure_for_data_lake(job, extracted, [DocumentCategory.SIGNALS])
        assert len(entries) == 1
        assert entries[0].data["direction"] == "input"


class TestStructureStates:
    def test_structures_states_and_transitions(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "states": [
                    {"state_id": "OFF", "code": "0x00", "name": "OFF"},
                    {"state_id": "RUN", "code": "0x02", "name": "RUN"},
                ],
                "transitions": [
                    {"from_state": "OFF", "to_state": "RUN", "condition": "IGN_SW=RUN"},
                ],
            },
            "metadata": {"document_id": "ES-001", "revision": "A"},
        }
        entries = structure_for_data_lake(job, extracted, [DocumentCategory.STATES])
        assert len(entries) == 3  # 2 states + 1 transition

    def test_multiple_transitions_between_same_states_get_unique_ids(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "transitions": [
                    {"from_state": "RUN_ENGINE", "to_state": "EMERGENCY",
                     "condition": "FAULT_CRITICAL = 1"},
                    {"from_state": "RUN_ENGINE", "to_state": "EMERGENCY",
                     "condition": "OIL_PRESS < 5 psi"},
                    {"from_state": "RUN_ENGINE", "to_state": "EMERGENCY",
                     "condition": "COOLANT_TEMP > 120C"},
                ],
            },
            "metadata": {"document_id": "ES-001", "revision": "A"},
        }
        entries = structure_for_data_lake(job, extracted, [DocumentCategory.STATES])
        ids = [e.entry_id for e in entries]
        assert len(ids) == len(set(ids))  # no collisions
        assert "TRANS-RUN_ENGINE-EMERGENCY-FAULT_CRITICAL_1" in ids

    def test_single_transition_keeps_clean_id(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "transitions": [
                    {"from_state": "OFF", "to_state": "ACC", "condition": "IGN_SW = ACC"},
                ],
            },
            "metadata": {"document_id": "ES-001", "revision": "A"},
        }
        entries = structure_for_data_lake(job, extracted, [DocumentCategory.STATES])
        assert entries[0].entry_id == "TRANS-OFF-ACC"


class TestStructureDTCs:
    def test_structures_dtcs(self) -> None:
        job = _make_job()
        extracted = {
            "entities": {
                "dtcs": [
                    {"code": "P0335", "description": "CKP Sensor", "mil": True},
                    {"code": "P0562", "description": "Low Voltage", "mil": True},
                ],
            },
            "metadata": {"document_id": "ES-001", "revision": "A"},
        }
        entries = structure_for_data_lake(job, extracted, [DocumentCategory.DTCS])
        assert len(entries) == 2
        assert entries[0].entry_id == "DTC-P0335"
