"""Source governance and evidence objects.

An ``EvidenceExcerpt`` is an immutable, exactly located quotation from a frozen synthetic
source. It is always labelled untrusted content: a citation is an evidence reference, not
an instruction.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.enums import (
    AuthorityClass,
    DataClassification,
    SourceLifecycle,
    TrustLabel,
)
from app.domain.limits import EXCERPT_MAX_CHARS
from app.schemas.base import HashStr, IdStr, StrictModel, VersionedRecord, VersionStr


class PageStructure(StrictModel):
    page_number: Annotated[int, Field(ge=1)]
    section_heading: str
    char_start: Annotated[int, Field(ge=0)]
    char_end: Annotated[int, Field(ge=0)]
    block_count: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def _ordered(self) -> PageStructure:
        if self.char_end < self.char_start:
            raise ValueError("char_end must not precede char_start")
        return self


class SourceRecord(VersionedRecord):
    source_id: IdStr
    source_version: VersionStr
    title: str
    owner: str
    authority_class: AuthorityClass
    lifecycle: SourceLifecycle
    effective_from: datetime
    effective_to: datetime | None = None
    business_scope_id: str
    permitted_use_case_ids: tuple[IdStr, ...]
    access_labels: tuple[str, ...]
    source_path: str
    source_sha256: HashStr
    extracted_text_sha256: HashStr
    page_structure: tuple[PageStructure, ...] = Field(min_length=1)
    supersedes: IdStr | None = None
    superseded_by: IdStr | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None
    quarantine_reason: str | None = None
    integrity_reference: str

    @property
    def source_key(self) -> str:
        return f"{self.source_id}@{self.source_version}"

    @model_validator(mode="after")
    def _lifecycle_consistency(self) -> SourceRecord:
        if self.lifecycle is SourceLifecycle.REVOKED and self.revoked_at is None:
            raise ValueError("a revoked source must record revoked_at")
        if self.lifecycle is SourceLifecycle.QUARANTINED and not self.quarantine_reason:
            raise ValueError("a quarantined source must record quarantine_reason")
        if self.lifecycle is SourceLifecycle.SUPERSEDED and not self.superseded_by:
            raise ValueError("a superseded source must record superseded_by")
        return self


class EvidenceExcerpt(VersionedRecord):
    """Immutable retrieved passage with exact location. Content is untrusted data."""

    excerpt_id: IdStr
    case_id: IdStr
    source_id: IdStr
    source_version: VersionStr
    page_number: Annotated[int, Field(ge=1)]
    section_heading: str
    block_index: Annotated[int, Field(ge=0)]
    char_start: Annotated[int, Field(ge=0)]
    char_end: Annotated[int, Field(ge=0)]
    text: Annotated[str, Field(max_length=EXCERPT_MAX_CHARS)]
    text_sha256: HashStr
    source_sha256: HashStr
    rank: Annotated[int, Field(ge=0)]
    retrieval_score: Annotated[int, Field(ge=0)] = 0
    trust_label: Literal[TrustLabel.UNTRUSTED_CONTENT] = TrustLabel.UNTRUSTED_CONTENT
    data_classification: Literal[DataClassification.SYNTHETIC_UNTRUSTED_CONTENT] = (
        DataClassification.SYNTHETIC_UNTRUSTED_CONTENT
    )
    instruction_like_flags: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _offsets_ordered(self) -> EvidenceExcerpt:
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    @property
    def citation_label(self) -> str:
        return (
            f"{self.source_id}@{self.source_version} p.{self.page_number} "
            f"[{self.char_start}-{self.char_end}]"
        )


class SourceEligibilityResult(StrictModel):
    source_id: IdStr
    source_version: VersionStr
    eligible: bool
    reason_code: str
    lifecycle: SourceLifecycle
    checked_at: datetime


class EvidencePlanItem(StrictModel):
    authority_class: AuthorityClass
    required: bool
    rationale: str


class ManifestEntry(StrictModel):
    source_id: IdStr
    source_version: VersionStr
    source_path: str
    source_sha256: HashStr
    lifecycle: SourceLifecycle
    active: bool
