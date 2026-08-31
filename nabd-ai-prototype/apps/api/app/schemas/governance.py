"""Control-plane fixtures: authorization decision, use-case contract and identity.

These objects are loaded from versioned repository data files. There is deliberately no
API that creates, edits or grants them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.enums import (
    AuthorizationStatus,
    DataClassification,
    DemoRole,
    IdentityStatus,
    OperationalStatus,
    StatusEvidence,
)
from app.schemas.base import IdStr, StrictModel, VersionedRecord, VersionStr


class AuthorizationDecision(VersionedRecord):
    """A synthetic test fixture. It is not human-owner approval or deployment authority."""

    authorization_id: IdStr
    fixture_notice: Literal[
        "TEST FIXTURE - synthetic demo authorization. Not human-owner approval, "
        "not deployment authorization, not production authority."
    ]
    environment_id: Literal["ISOLATED_PROTOTYPE_V1"]
    data_boundary_id: Literal["SYNTHETIC_ONLY"]
    business_scope_id: Literal["BUSINESS_UNIT_V1"]
    use_case_contract_id: IdStr
    source_manifest_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    allowed_component_versions: dict[str, VersionStr]
    allowed_role_ids: tuple[IdStr, ...] = Field(min_length=1)
    allowed_model_configuration_ids: tuple[IdStr, ...] = Field(min_length=1)
    demo_period_start: datetime
    demo_period_end: datetime
    authorization_status: Literal[AuthorizationStatus.NOT_GRANTED] = AuthorizationStatus.NOT_GRANTED
    revoked: bool = False

    @model_validator(mode="after")
    def _period_ordered(self) -> AuthorizationDecision:
        if self.demo_period_end <= self.demo_period_start:
            raise ValueError("demo_period_end must be after demo_period_start")
        return self

    def is_current(self, at: datetime) -> bool:
        return (not self.revoked) and self.demo_period_start <= at <= self.demo_period_end


class UseCaseContract(VersionedRecord):
    """The single bounded V1 question contract and its exclusions."""

    use_case_contract_id: IdStr
    title_en: str
    title_ar: str
    description_en: str
    description_ar: str
    permitted_purpose: IdStr
    permitted_question_kinds: tuple[str, ...] = Field(min_length=1)
    required_source_authority_classes: tuple[str, ...] = Field(min_length=1)
    excluded_scope_terms: tuple[str, ...] = Field(min_length=1)
    excluded_outcomes: tuple[str, ...] = Field(min_length=1)
    max_question_chars: int = Field(ge=1)
    business_scope_id: Literal["BUSINESS_UNIT_V1"]
    data_boundary_id: Literal["SYNTHETIC_ONLY"]


class DemoIdentity(VersionedRecord):
    """A seeded synthetic identity. Never a real person and never an IdP subject."""

    identity_id: IdStr
    display_name_en: str
    display_name_ar: str
    role: DemoRole
    role_id: IdStr
    business_scope_id: str
    status: IdentityStatus
    capabilities: tuple[str, ...]
    prohibitions: tuple[str, ...]
    selectable_in_ui: bool = True
    notes_en: str = ""


class IdentityAssertion(VersionedRecord):
    """Server-derived identity for one request. The browser never supplies these fields."""

    assertion_id: IdStr
    session_id: IdStr
    identity_id: IdStr
    role: DemoRole
    role_id: IdStr
    business_scope_id: str
    status: IdentityStatus
    issued_at: datetime
    expires_at: datetime
    data_classification: DataClassification = DataClassification.SYNTHETIC_PROTOTYPE

    def is_valid_at(self, at: datetime) -> bool:
        return self.status is IdentityStatus.ACTIVE and self.issued_at <= at < self.expires_at


class StatusRecord(VersionedRecord):
    """The four independent status dimensions. They are never merged into one value."""

    status_record_id: IdStr
    component_id: IdStr
    component_version: VersionStr
    built: StatusEvidence = StatusEvidence.NOT_EVIDENCED
    integration: StatusEvidence = StatusEvidence.NOT_EVIDENCED
    operational: OperationalStatus = OperationalStatus.NOT_EVIDENCED
    authorization: AuthorizationStatus = AuthorizationStatus.NOT_GRANTED
    narrow_claim: str
    limitations: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    accepted_by: str | None = None
    accepted_at: datetime | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def _no_self_certification(self) -> StatusRecord:
        if self.accepted_by is not None and self.accepted_by == self.produced_by:
            raise ValueError("a record cannot accept its own status claim (INV-16)")
        return self


class KillSwitchState(StrictModel):
    active: bool
    changed_at: datetime | None = None
    changed_by: IdStr | None = None
    reason: str | None = None
