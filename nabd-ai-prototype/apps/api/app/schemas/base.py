"""Shared model base classes.

Every privileged boundary object forbids unknown fields. A model, a source document or a
browser cannot introduce a field that the control plane did not declare.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.domain.canonical import format_timestamp, normalise_text, utc_now
from app.domain.enums import DataClassification
from app.domain.versions import SCHEMA_VERSION

# Identifiers cover fixture IDs, synthetic identity addresses (``name@demo.nabd.local``),
# source keys (``POL-001@v1``) and provenance paths (``build:data/fixtures/...``). No
# whitespace, quoting or control characters are admissible.
IdStr = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:@/+\-]+$")]
HashStr = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
VersionStr = Annotated[str, Field(min_length=1, max_length=64)]


class StrictModel(BaseModel):
    """Closed schema: unknown keys are a validation error, never a silent drop."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=False,
        validate_assignment=True,
        populate_by_name=True,
        protected_namespaces=(),
    )

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize_datetimes(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return format_timestamp(value)
        return value

    def canonical_dict(self) -> dict[str, Any]:
        """Plain-Python view suitable for canonical JSON serialization."""
        return self.model_dump(mode="json", by_alias=False)


class VersionedRecord(StrictModel):
    """Base for persisted governed records."""

    schema_version: VersionStr = SCHEMA_VERSION
    created_at: datetime = Field(default_factory=utc_now)
    data_classification: DataClassification = DataClassification.SYNTHETIC_PROTOTYPE
    produced_by: IdStr = Field(
        description="Actor or service provenance for this record.",
    )


class UntrustedText(StrictModel):
    """Wrapper marking a value as data-plane content that is never an instruction."""

    trust_label: str = Field(default="UNTRUSTED_CONTENT", frozen=True)
    text: str

    @property
    def normalised(self) -> str:
        return normalise_text(self.text)
