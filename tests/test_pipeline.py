"""Tests for the document processing pipeline."""

from __future__ import annotations

from pathlib import Path

from pipeline.classify import classify_document
from pipeline.extract import extract_content
from pipeline.ingest import ingest_file
from pipeline.integrate import integrate_to_data_lake
from pipeline.models import DocumentCategory, PipelineStage
from pipeline.structure import structure_for_data_lake
from pipeline.validate import validate_entries


class TestIngest:
    def test_ingest_creates_job(self, tmp_source_dir: Path) -> None:
        json_file = tmp_source_dir / "test_spec.extracted.json"
        job = ingest_file(json_file)
        assert job.job_id.startswith("JOB-")
        assert job.filename == "test_spec.extracted.json"
        assert job.file_type == "extracted_json"
        assert job.current_stage == PipelineStage.RECEIVED

    def test_ingest_detects_file_types(self, tmp_path: Path) -> None:
        for suffix, expected in [(".json", "extracted_json"), (".md", "markdown_spec"),
                                  (".xlsx", "excel_workbook"), (".txt", "unknown")]:
            f = tmp_path / f"test{suffix}"
            f.write_text("test")
            job = ingest_file(f)
            assert job.file_type == expected


class TestExtract:
    def test_extract_from_json(self, tmp_source_dir: Path) -> None:
        json_file = tmp_source_dir / "test_spec.extracted.json"
        job = ingest_file(json_file)
        extracted = extract_content(job, json_file)
        assert "states" in extracted["entities"]
        assert len(extracted["entities"]["states"]) == 2
        assert "transitions" in extracted["entities"]
        assert extracted["tables"] == 2

    def test_extract_from_markdown(self, tmp_path: Path) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("# Heading\n| Col1 | Col2 |\n|---|---|\n| A | B |\n")
        job = ingest_file(md_file)
        extracted = extract_content(job, md_file)
        assert len(extracted["raw_sections"]) > 0


class TestClassify:
    def test_classify_states(self, tmp_source_dir: Path) -> None:
        json_file = tmp_source_dir / "test_spec.extracted.json"
        job = ingest_file(json_file)
        extracted = extract_content(job, json_file)
        categories = classify_document(job, extracted)
        assert DocumentCategory.STATES in categories
        assert DocumentCategory.DTCS in categories


class TestStructure:
    def test_structure_creates_entries(self, tmp_source_dir: Path) -> None:
        json_file = tmp_source_dir / "test_spec.extracted.json"
        job = ingest_file(json_file)
        extracted = extract_content(job, json_file)
        categories = classify_document(job, extracted)
        entries = structure_for_data_lake(job, extracted, categories)
        assert len(entries) > 0
        assert any(e.category == DocumentCategory.STATES for e in entries)
        assert any(e.category == DocumentCategory.DTCS for e in entries)


class TestValidate:
    def test_validate_all_new(self, tmp_source_dir: Path) -> None:
        json_file = tmp_source_dir / "test_spec.extracted.json"
        job = ingest_file(json_file)
        extracted = extract_content(job, json_file)
        categories = classify_document(job, extracted)
        entries = structure_for_data_lake(job, extracted, categories)
        findings = validate_entries(job, entries)
        assert all(f["type"] == "new" for f in findings)


class TestIntegrate:
    def test_integrate_writes_files(self, tmp_source_dir: Path) -> None:
        json_file = tmp_source_dir / "test_spec.extracted.json"
        job = ingest_file(json_file)
        extracted = extract_content(job, json_file)
        categories = classify_document(job, extracted)
        entries = structure_for_data_lake(job, extracted, categories)
        findings = validate_entries(job, entries)
        paths = integrate_to_data_lake(job, entries, findings)
        assert len(paths) > 0
        for p in paths:
            assert Path(p).exists()


class TestFullPipeline:
    def test_end_to_end(self, tmp_source_dir: Path) -> None:
        from pipeline.orchestrator import process_document

        json_file = tmp_source_dir / "test_spec.extracted.json"
        job = process_document(json_file, update_state=False)
        assert job.current_stage == PipelineStage.INTEGRATED
        assert len(job.data_lake_paths) > 0
        assert len(job.categories) > 0
        assert sum(job.extracted_entities.values()) > 0
