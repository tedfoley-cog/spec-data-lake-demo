"""Data models for the document processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PipelineStage(Enum):
    """Stages of the document processing pipeline."""

    RECEIVED = "received"
    EXTRACTING = "extracting"
    CLASSIFYING = "classifying"
    STRUCTURING = "structuring"
    VALIDATING = "validating"
    INTEGRATED = "integrated"
    FAILED = "failed"


class DocumentCategory(Enum):
    """Categories of structured data in the data lake."""

    SIGNALS = "signals"
    STATES = "states"
    REQUIREMENTS = "requirements"
    DTCS = "dtcs"
    PARAMETERS = "parameters"
    RELATIONSHIPS = "relationships"


@dataclass
class PipelineEvent:
    """A single event in the processing pipeline."""

    stage: PipelineStage
    timestamp: str = ""
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class DocumentJob:
    """A document being processed through the pipeline."""

    job_id: str
    filename: str
    file_size: int = 0
    file_type: str = ""
    current_stage: PipelineStage = PipelineStage.RECEIVED
    events: list[PipelineEvent] = field(default_factory=list)
    extracted_entities: dict[str, int] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)
    data_lake_paths: list[str] = field(default_factory=list)
    error: str = ""

    def advance(self, stage: PipelineStage, message: str = "", **details: Any) -> None:
        """Advance to the next pipeline stage."""
        self.current_stage = stage
        self.events.append(PipelineEvent(stage=stage, message=message, details=details))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "current_stage": self.current_stage.value,
            "events": [
                {
                    "stage": e.stage.value,
                    "timestamp": e.timestamp,
                    "message": e.message,
                    "details": e.details,
                }
                for e in self.events
            ],
            "extracted_entities": self.extracted_entities,
            "categories": self.categories,
            "data_lake_paths": self.data_lake_paths,
            "error": self.error,
        }


@dataclass
class DataLakeEntry:
    """An entry in the structured data lake."""

    entry_id: str
    category: DocumentCategory
    source_document: str
    source_revision: str
    data: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "entry_id": self.entry_id,
            "category": self.category.value,
            "source_document": self.source_document,
            "source_revision": self.source_revision,
            "data": self.data,
            "created_at": self.created_at,
            "version": self.version,
        }
