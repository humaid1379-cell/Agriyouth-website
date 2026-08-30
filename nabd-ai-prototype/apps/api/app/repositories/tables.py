"""Relational schema.

Normalised tables with JSONB payload snapshots for versioned governed records. Confirmed
audit events are append-only: the migration installs a PostgreSQL trigger that rejects
``UPDATE`` and ``DELETE``, and the application role is granted ``INSERT``/``SELECT`` only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.canonical import utc_now
from app.repositories.database import Base, JsonPayload


def _ts() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class DemoIdentityRow(Base):
    __tablename__ = "demo_identities"

    identity_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    role_id: Mapped[str] = mapped_column(String(64), nullable=False)
    business_scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    selectable_in_ui: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class DemoSessionRow(Base):
    __tablename__ = "demo_sessions"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    identity_id: Mapped[str] = mapped_column(
        ForeignKey("demo_identities.identity_id"), nullable=False, index=True
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    token_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = _ts()


class AuthorizationDecisionRow(Base):
    __tablename__ = "authorization_decisions"

    authorization_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    environment_id: Mapped[str] = mapped_column(String(64), nullable=False)
    use_case_contract_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    demo_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    demo_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class UseCaseContractRow(Base):
    __tablename__ = "use_case_contracts"

    use_case_contract_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    business_scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class SourceRecordRow(Base):
    __tablename__ = "source_records"

    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(Text, nullable=False)
    authority_class: Mapped[str] = mapped_column(String(48), nullable=False)
    business_scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = _ts()

    versions: Mapped[list[SourceVersionRow]] = relationship(back_populates="source")


class SourceVersionRow(Base):
    __tablename__ = "source_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "source_version", name="uq_source_versions_source_id"),
        Index("ix_source_versions_lifecycle", "lifecycle"),
    )

    source_version_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_records.source_id"), nullable=False)
    source_version: Mapped[str] = mapped_column(String(32), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(16), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by: Mapped[str | None] = mapped_column(String(128))
    quarantine_reason: Mapped[str | None] = mapped_column(Text)
    business_scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    access_labels: Mapped[list[str]] = mapped_column(JsonPayload, nullable=False)
    permitted_use_case_ids: Mapped[list[str]] = mapped_column(JsonPayload, nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    instruction_like_flags: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()

    source: Mapped[SourceRecordRow] = relationship(back_populates="versions")
    pages: Mapped[list[SourcePageRow]] = relationship(back_populates="version")


class SourcePageRow(Base):
    __tablename__ = "source_pages"
    __table_args__ = (
        UniqueConstraint(
            "source_version_key", "page_number", name="uq_source_pages_source_version_key"
        ),
    )

    source_page_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    source_version_key: Mapped[str] = mapped_column(
        ForeignKey("source_versions.source_version_key"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section_headings: Mapped[list[str]] = mapped_column(JsonPayload, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    block_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_text: Mapped[str] = mapped_column(Text, nullable=False)

    version: Mapped[SourceVersionRow] = relationship(back_populates="pages")
    blocks: Mapped[list[SourceBlockRow]] = relationship(back_populates="page")


class SourceBlockRow(Base):
    """Retrievable unit. The lexical index is built over this table only."""

    __tablename__ = "source_blocks"
    __table_args__ = (
        Index("ix_source_blocks_version", "source_version_key"),
        Index("ix_source_blocks_page", "source_page_id"),
    )

    source_block_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    source_page_id: Mapped[str] = mapped_column(
        ForeignKey("source_pages.source_page_id"), nullable=False
    )
    source_version_key: Mapped[str] = mapped_column(
        ForeignKey("source_versions.source_version_key"), nullable=False
    )
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section_heading: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    instruction_like_flags: Mapped[list[str]] = mapped_column(JsonPayload, nullable=False)

    page: Mapped[SourcePageRow] = relationship(back_populates="blocks")


class CaseRow(Base):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_requester", "requester_identity_id"),
        Index("ix_cases_state", "current_state"),
    )

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    requester_identity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    business_scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    use_case_contract_id: Mapped[str] = mapped_column(String(128), nullable=False)
    authorization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_question: Mapped[str] = mapped_column(Text, nullable=False)
    normalised_question: Mapped[str] = mapped_column(Text, nullable=False)
    question_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    current_state: Mapped[str] = mapped_column(String(48), nullable=False)
    route: Mapped[str | None] = mapped_column(String(32))
    reason_code: Mapped[str | None] = mapped_column(String(64))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_record: Mapped[dict[str, Any] | None] = mapped_column(JsonPayload)
    created_at: Mapped[datetime] = _ts()
    updated_at: Mapped[datetime] = _ts()


class CaseStateTransitionRow(Base):
    __tablename__ = "case_state_transitions"
    __table_args__ = (
        UniqueConstraint("case_id", "sequence", name="uq_case_state_transitions_case_id"),
        Index("ix_case_state_transitions_case", "case_id"),
    )

    transition_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    from_state: Mapped[str | None] = mapped_column(String(48))
    to_state: Mapped[str] = mapped_column(String(48), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    component_versions: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    applicable_rule_versions: Mapped[list[str]] = mapped_column(JsonPayload, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModelConfigurationRow(Base):
    __tablename__ = "model_configurations"

    model_configuration_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    task_role: Mapped[str] = mapped_column(String(16), nullable=False)
    model_revision: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class ModelRunRow(Base):
    __tablename__ = "model_runs"
    __table_args__ = (
        UniqueConstraint("case_id", "task_role", "call_index", name="uq_model_runs_case_id"),
        CheckConstraint("call_index >= 1 AND call_index <= 2", name="call_index_within_budget"),
        CheckConstraint("retry_count >= 0 AND retry_count <= 1", name="retry_within_budget"),
    )

    model_run_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False, index=True)
    model_configuration_id: Mapped[str] = mapped_column(String(128), nullable=False)
    task_role: Mapped[str] = mapped_column(String(16), nullable=False)
    call_index: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    output_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    input_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    output_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class EvidenceExcerptRow(Base):
    __tablename__ = "evidence_excerpts"
    __table_args__ = (
        Index("ix_evidence_excerpts_case", "case_id"),
        UniqueConstraint("case_id", "excerpt_id", name="uq_evidence_excerpts_case_id"),
    )

    excerpt_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source_version_key: Mapped[str] = mapped_column(String(128), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section_heading: Mapped[str] = mapped_column(Text, nullable=False)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    retrieval_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    admitted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class GeneratedClaimRow(Base):
    __tablename__ = "generated_claims"
    __table_args__ = (UniqueConstraint("case_id", "claim_ref", name="uq_generated_claims_case_id"),)

    claim_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False, index=True)
    claim_ref: Mapped[str] = mapped_column(String(8), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    materiality: Mapped[str] = mapped_column(String(16), nullable=False)
    support_state: Mapped[str] = mapped_column(String(24), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class ClaimEvidenceLinkRow(Base):
    __tablename__ = "claim_evidence_links"
    __table_args__ = (
        UniqueConstraint("claim_id", "excerpt_id", name="uq_claim_evidence_links_claim_id"),
    )

    claim_evidence_link_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("generated_claims.claim_id"), nullable=False)
    excerpt_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_excerpts.excerpt_id"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quote_start: Mapped[int] = mapped_column(Integer, nullable=False)
    quote_end: Mapped[int] = mapped_column(Integer, nullable=False)
    quoted_text: Mapped[str] = mapped_column(Text, nullable=False)
    quote_verified: Mapped[bool] = mapped_column(Boolean, nullable=False)


class DeterministicResultRow(Base):
    __tablename__ = "deterministic_results"
    __table_args__ = (Index("ix_deterministic_results_case", "case_id"),)

    deterministic_result_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    effect: Mapped[str] = mapped_column(String(32), nullable=False)
    precedence_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)


class UncertaintyRecordRow(Base):
    __tablename__ = "uncertainty_records"
    __table_args__ = (Index("ix_uncertainty_records_case", "case_id"),)

    uncertainty_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class DecisionPacketRow(Base):
    __tablename__ = "decision_packets"
    __table_args__ = (
        UniqueConstraint("case_id", "packet_version", name="uq_decision_packets_case_id"),
        Index("ix_decision_packets_case", "case_id"),
    )

    packet_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    packet_version: Mapped[int] = mapped_column(Integer, nullable=False)
    route: Mapped[str] = mapped_column(String(32), nullable=False)
    packet_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    # The hash as sealed at pre-issuance. It is what the confirmed audit event binds and
    # what a reviewer disposes of; it never changes once issued.
    issued_sha256: Mapped[str | None] = mapped_column(String(64))
    canonical_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    pre_issuance_event_id: Mapped[str | None] = mapped_column(String(96))
    displayable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    superseded_by_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _ts()


class HumanDispositionRow(Base):
    __tablename__ = "human_dispositions"
    __table_args__ = (
        # Exactly one final accepted/rejected test disposition per exact packet version.
        # Non-final attempts (returns for clarification, denied attempts) stay auditable.
        Index(
            "uq_human_dispositions_final_per_packet",
            "packet_id",
            "packet_version",
            unique=True,
            postgresql_where=text("is_final"),
            sqlite_where=text("is_final = 1"),
        ),
    )

    disposition_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False, index=True)
    packet_id: Mapped[str] = mapped_column(String(96), nullable=False)
    packet_version: Mapped[int] = mapped_column(Integer, nullable=False)
    packet_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer_identity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    disposition_value: Mapped[str] = mapped_column(String(32), nullable=False)
    human_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closure_event_id: Mapped[str | None] = mapped_column(String(96))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)


class AuditEventRow(Base):
    """Append-only. ``UPDATE``/``DELETE`` are rejected by trigger and by role grants."""

    __tablename__ = "audit_events"
    __table_args__ = (
        UniqueConstraint("chain_key", "sequence", name="uq_audit_events_chain_key"),
        Index("ix_audit_events_case", "case_id"),
        Index("ix_audit_events_type", "event_type"),
    )

    event_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    chain_key: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(64))
    application_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    severity: Mapped[str | None] = mapped_column(String(16))
    from_state: Mapped[str | None] = mapped_column(String(48))
    to_state: Mapped[str | None] = mapped_column(String(48))
    previous_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class KillSwitchEventRow(Base):
    __tablename__ = "kill_switch_events"

    kill_switch_event_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TevvRunRow(Base):
    __tablename__ = "tevv_runs"

    tevv_run_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    plan_version: Mapped[str] = mapped_column(String(48), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executor: Mapped[str] = mapped_column(String(128), nullable=False)
    component_versions: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    summary: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(Text)


class TevvResultRow(Base):
    __tablename__ = "tevv_results"
    __table_args__ = (
        UniqueConstraint(
            "tevv_run_id", "scenario_id", "repetition", name="uq_tevv_results_tevv_run_id"
        ),
    )

    tevv_result_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    tevv_run_id: Mapped[str] = mapped_column(ForeignKey("tevv_runs.tevv_run_id"), nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(32), nullable=False)
    repetition: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    expected: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    actual: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(64))
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    defect_ids: Mapped[list[str]] = mapped_column(JsonPayload, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DefectRow(Base):
    __tablename__ = "defects"

    defect_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvidenceRecordRow(Base):
    __tablename__ = "evidence_records"

    evidence_record_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    component_id: Mapped[str] = mapped_column(String(96), nullable=False)
    component_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status_dimension: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()


class StatusRecordRow(Base):
    __tablename__ = "status_records"

    status_record_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    component_id: Mapped[str] = mapped_column(String(96), nullable=False)
    component_version: Mapped[str] = mapped_column(String(64), nullable=False)
    built: Mapped[str] = mapped_column(String(24), nullable=False)
    integration: Mapped[str] = mapped_column(String(24), nullable=False)
    operational: Mapped[str] = mapped_column(String(24), nullable=False)
    authorization: Mapped[str] = mapped_column(String(24), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonPayload, nullable=False)
    created_at: Mapped[datetime] = _ts()
