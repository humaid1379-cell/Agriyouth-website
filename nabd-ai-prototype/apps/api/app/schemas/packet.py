"""The Decision Readiness Packet, its sections, and the human disposition bound to it.

The canonical JSON packet is the governed artifact. An HTML view or print export is a
derived, read-only rendering and never a substitute for this object.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.canonical import HASH_ALGORITHM, PROFILE_ID, VERIFIER_METHOD
from app.domain.enums import (
    AuthorizationStatus,
    DataClassification,
    DemoRole,
    DispositionValue,
    OperationalStatus,
    RiskLevel,
    Route,
    StatusEvidence,
)
from app.domain.limits import RATIONALE_MIN_CHARS
from app.schemas.base import HashStr, IdStr, StrictModel, VersionedRecord, VersionStr
from app.schemas.evidence import EvidenceExcerpt
from app.schemas.reasoning import (
    DeterministicResult,
    GeneratedClaim,
    RiskProfile,
    UncertaintyRecord,
)


class PacketIdentity(StrictModel):
    packet_id: IdStr
    packet_version: Annotated[int, Field(ge=1)]
    case_id: IdStr
    schema_id: Literal["decision-readiness-packet-v1"] = "decision-readiness-packet-v1"
    data_classification: Literal[DataClassification.SYNTHETIC_PROTOTYPE] = (
        DataClassification.SYNTHETIC_PROTOTYPE
    )
    environment_id: Literal["ISOLATED_PROTOTYPE_V1"] = "ISOLATED_PROTOTYPE_V1"
    business_scope_id: Literal["BUSINESS_UNIT_V1"] = "BUSINESS_UNIT_V1"
    data_boundary_id: Literal["SYNTHETIC_ONLY"] = "SYNTHETIC_ONLY"
    created_at: datetime
    supersedes_packet_id: IdStr | None = None


class PacketAuthorizationContext(StrictModel):
    authorization_id: IdStr
    fixture_notice: str
    use_case_contract_id: IdStr
    demo_period_start: datetime
    demo_period_end: datetime
    authorization_status: Literal[AuthorizationStatus.NOT_GRANTED] = AuthorizationStatus.NOT_GRANTED
    source_manifest_sha256: HashStr


class PacketRequestContext(StrictModel):
    requester_identity_id: IdStr
    requester_role: DemoRole
    submitted_at: datetime
    normalised_question: str
    permitted_purpose: IdStr
    question_sha256: HashStr


class PacketEvidenceManifestItem(StrictModel):
    excerpt_id: IdStr
    source_id: IdStr
    source_version: VersionStr
    authority_class: str
    page_number: Annotated[int, Field(ge=1)]
    section_heading: str
    char_start: Annotated[int, Field(ge=0)]
    char_end: Annotated[int, Field(ge=0)]
    excerpt_sha256: HashStr
    source_sha256: HashStr
    retrieved_at: datetime
    trust_label: Literal["UNTRUSTED_CONTENT"] = "UNTRUSTED_CONTENT"


class PacketVersionLineage(StrictModel):
    workflow_version: VersionStr
    schema_version: VersionStr
    rule_catalog_version: VersionStr
    corpus_version: VersionStr
    retrieval_version: VersionStr
    prompt_draft_version: VersionStr
    prompt_verify_version: VersionStr
    packet_schema_version: VersionStr
    audit_chain_version: VersionStr
    draft_model_configuration_id: IdStr
    verifier_model_configuration_id: IdStr
    canonical_json_profile: Literal["nabd-canonical-json-v1"] = "nabd-canonical-json-v1"


class PacketIntegrity(StrictModel):
    canonical_json_profile: Literal["nabd-canonical-json-v1"] = PROFILE_ID  # type: ignore[assignment]
    hash_algorithm: Literal["SHA-256"] = HASH_ALGORITHM  # type: ignore[assignment]
    verifier_method: Literal["recompute-canonical-json-sha256"] = VERIFIER_METHOD  # type: ignore[assignment]
    calculated_at: datetime
    packet_sha256: HashStr = "0" * 64
    tamper_evidence_note: str = (
        "This SHA-256 is a tamper-evidence reference over the canonical packet preimage. "
        "It is not proof of truth, immutable storage, authorization, or authorship."
    )


class PacketAuditBinding(StrictModel):
    pre_issuance_event_id: IdStr | None = None
    pre_issuance_confirmed_at: datetime | None = None
    disposition_closure_event_id: IdStr | None = None
    disposition_closure_confirmed_at: datetime | None = None
    audit_chain_head_hash: HashStr | None = None


class PacketNotice(StrictModel):
    notice_id: IdStr
    template_version: VersionStr
    heading_en: str
    text_en: str
    heading_ar: str
    text_ar: str


class PacketStatusBlock(StrictModel):
    """Four independent dimensions. Never rendered as one merged status."""

    built: StatusEvidence = StatusEvidence.NOT_EVIDENCED
    integration: StatusEvidence = StatusEvidence.NOT_EVIDENCED
    operational: OperationalStatus = OperationalStatus.NOT_EVIDENCED
    authorization: AuthorizationStatus = AuthorizationStatus.NOT_GRANTED


class HumanDisposition(VersionedRecord):
    """A test-only reviewer disposition. It never unlocks an execution path."""

    disposition_id: IdStr
    case_id: IdStr
    packet_id: IdStr
    packet_version: Annotated[int, Field(ge=1)]
    packet_sha256: HashStr
    reviewer_identity_id: IdStr
    reviewer_role: Literal[DemoRole.REVIEWER] = DemoRole.REVIEWER
    reviewer_role_id: IdStr
    disposition_value: DispositionValue
    human_rationale: Annotated[str, Field(min_length=RATIONALE_MIN_CHARS, max_length=4000)]
    decided_at: datetime
    sod_check_passed: Literal[True] = True
    authority_reverified_at: datetime
    is_final: bool
    non_execution_notice: Literal[
        "This disposition records test evidence only. It does not approve, execute, "
        "transmit, or activate any institutional action."
    ] = (
        "This disposition records test evidence only. It does not approve, execute, "
        "transmit, or activate any institutional action."
    )

    @model_validator(mode="after")
    def _rationale_is_substantive(self) -> HumanDisposition:
        if not self.human_rationale.strip():
            raise ValueError("human_rationale must not be blank")
        return self


class DecisionReadinessPacket(StrictModel):
    """The canonical governed artifact."""

    identity: PacketIdentity
    authorization_context: PacketAuthorizationContext
    request_context: PacketRequestContext
    evidence_manifest: tuple[PacketEvidenceManifestItem, ...]
    claim_ledger: tuple[GeneratedClaim, ...]
    rule_results: tuple[DeterministicResult, ...] = Field(min_length=1)
    uncertainty: tuple[UncertaintyRecord, ...]
    conflicts: tuple[str, ...]
    risk: RiskProfile
    limitations: tuple[str, ...] = Field(min_length=1)
    route: Route
    route_reason_code: str
    version_lineage: PacketVersionLineage
    integrity: PacketIntegrity
    audit_binding: PacketAuditBinding
    notices: tuple[PacketNotice, ...] = Field(min_length=4)
    prototype_status: PacketStatusBlock = PacketStatusBlock()
    disposition: HumanDisposition | None = None

    @model_validator(mode="after")
    def _route_invariants(self) -> DecisionReadinessPacket:
        if self.route is Route.CANNOT_PROCEED and self.disposition is not None:
            raise ValueError("a CANNOT_PROCEED packet cannot carry a disposition")
        return self

    @property
    def risk_level(self) -> RiskLevel:
        return self.risk.inherent_risk


class StopRecord(VersionedRecord):
    """A terminal ``CANNOT_PROCEED`` record. It is not a packet and is never displayed as one."""

    stop_record_id: IdStr
    case_id: IdStr
    failed_state: str
    reason_code: str
    message: str
    rule_results: tuple[DeterministicResult, ...] = ()
    uncertainty: tuple[UncertaintyRecord, ...] = ()
    occurred_at: datetime
    route: Literal[Route.CANNOT_PROCEED] = Route.CANNOT_PROCEED


class EvidenceRecord(VersionedRecord):
    """An assurance evidence artifact reference for the evidence register."""

    evidence_record_id: IdStr
    component_id: IdStr
    component_version: VersionStr
    status_dimension: str
    evidence_type: str
    artifact_path: str
    artifact_sha256: HashStr
    environment_id: str
    period_start: datetime
    period_end: datetime | None = None
    narrow_claim: str
    limitations: tuple[str, ...]
    preparer: str
    evaluator: str | None = None
    acceptor: str | None = None
    decision: str = "NOT_ACCEPTED"
    expires_at: datetime | None = None
    revocation_path: str = ""

    @model_validator(mode="after")
    def _three_function_separation(self) -> EvidenceRecord:
        parties = [p for p in (self.preparer, self.evaluator, self.acceptor) if p]
        if len(parties) == 3 and len(set(parties)) < 3:
            raise ValueError(
                "preparer, evaluator and acceptor must be three distinct identities (INV-16)"
            )
        return self
