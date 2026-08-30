"""API request and response contracts.

Request models are deliberately narrow. A client can choose a demo identity, submit one
question, and submit one disposition with a rationale. It cannot supply a role, a scope, an
authority claim, a route, a rule outcome, a model configuration or a fault profile.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import Field

from app.domain.enums import DemoRole, DispositionValue
from app.domain.limits import QUESTION_MAX_CHARS, RATIONALE_MIN_CHARS
from app.schemas.base import IdStr, StrictModel


class ErrorBody(StrictModel):
    code: str
    message: str
    case_id: str | None = None
    state: str | None = None
    correlation_id: str
    safe_to_display: bool


class ErrorEnvelope(StrictModel):
    error: ErrorBody


class DemoSessionRequest(StrictModel):
    identity_id: IdStr


class NoticePayload(StrictModel):
    notice_id: str
    heading_en: str
    text_en: str
    heading_ar: str
    text_ar: str


class DemoSessionResponse(StrictModel):
    token: str
    identity_id: str
    role: DemoRole
    expires_at: datetime
    notices: tuple[NoticePayload, ...]


class DemoIdentityOption(StrictModel):
    identity_id: str
    display_name_en: str
    display_name_ar: str
    role: DemoRole
    capabilities: tuple[str, ...]
    prohibitions: tuple[str, ...]


class MeResponse(StrictModel):
    identity_id: str
    display_name_en: str
    display_name_ar: str
    role: DemoRole
    role_id: str
    business_scope_id: str
    environment_id: str
    data_boundary_id: str
    session_expires_at: datetime
    capabilities: tuple[str, ...]
    prohibitions: tuple[str, ...]
    notices: tuple[NoticePayload, ...]
    brand_statement_en: str
    brand_statement_ar: str


class UseCaseResponse(StrictModel):
    use_case_contract_id: str
    title_en: str
    title_ar: str
    description_en: str
    description_ar: str
    permitted_purpose: str
    permitted_question_kinds: tuple[str, ...]
    excluded_scope_terms: tuple[str, ...]
    excluded_outcomes: tuple[str, ...]
    max_question_chars: int
    min_question_chars: int
    business_scope_id: str
    data_boundary_id: str


class CreateCaseRequest(StrictModel):
    question: Annotated[str, Field(min_length=1, max_length=QUESTION_MAX_CHARS)]


class CaseSummary(StrictModel):
    case_id: str
    requester_identity_id: str
    normalised_question: str
    current_state: str
    stage: int | None
    route: str | None
    reason_code: str | None
    reason_message: str | None
    submitted_at: datetime
    updated_at: datetime
    packet_available: bool
    permissible_next_actions: tuple[str, ...]


class CaseListResponse(StrictModel):
    cases: tuple[CaseSummary, ...]


class StateTransitionView(StrictModel):
    sequence: int
    from_state: str | None
    to_state: str
    reason_code: str | None
    reason_message: str | None
    actor_id: str
    occurred_at: datetime


class RuleResultView(StrictModel):
    rule_id: str
    rule_version: str
    outcome: str
    reason_code: str
    effect: str
    precedence_rank: int
    detail: str
    evaluated_at: datetime


class CaseProgressResponse(StrictModel):
    case: CaseSummary
    transitions: tuple[StateTransitionView, ...]
    rule_results: tuple[RuleResultView, ...]
    limits: tuple[dict[str, Any], ...]
    stop_record: dict[str, Any] | None


class PacketResponse(StrictModel):
    packet: dict[str, Any]
    canonical_sha256: str
    seal_verified: bool


class ExcerptResponse(StrictModel):
    excerpt_id: str
    case_id: str
    source_id: str
    source_version: str
    source_title: str
    authority_class: str
    lifecycle: str
    page_number: int
    section_heading: str
    char_start: int
    char_end: int
    text: str
    text_sha256: str
    source_sha256: str
    trust_label: str
    citation_label: str
    revocation_warning: str | None


class SourcePageResponse(StrictModel):
    source_id: str
    source_version: str
    title: str
    lifecycle: str
    page_number: int
    page_count: int
    section_headings: tuple[str, ...]
    char_start: int
    char_end: int
    text: str
    trust_label: str
    revocation_warning: str | None


class DispositionRequest(StrictModel):
    disposition_value: DispositionValue
    human_rationale: Annotated[str, Field(min_length=RATIONALE_MIN_CHARS, max_length=4000)]
    packet_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None


class DispositionResponse(StrictModel):
    case_id: str
    disposition_id: str
    disposition_value: DispositionValue
    is_final: bool
    terminal_state: str
    closure_event_id: str
    packet_sha256: str
    non_execution_notice: str


class AuditEventView(StrictModel):
    event_id: str
    sequence: int
    event_type: str
    application_time: datetime
    actor_id: str
    actor_kind: str
    outcome: str
    reason_code: str | None
    severity: str | None
    from_state: str | None
    to_state: str | None
    object_kind: str | None
    object_id: str | None
    previous_event_hash: str
    event_hash: str
    confirmed: bool


class AuditResponse(StrictModel):
    case_id: str
    events: tuple[AuditEventView, ...]
    verification: dict[str, Any]


class LineageNode(StrictModel):
    node_id: str
    kind: str
    label: str
    detail: str = ""


class LineageEdge(StrictModel):
    source: str
    target: str
    relation: str


class LineageResponse(StrictModel):
    case_id: str
    nodes: tuple[LineageNode, ...]
    edges: tuple[LineageEdge, ...]


class KillSwitchRequest(StrictModel):
    active: bool
    reason: Annotated[str, Field(min_length=10, max_length=500)]


class KillSwitchResponse(StrictModel):
    active: bool
    changed_at: datetime | None
    changed_by: str | None
    reason: str | None


class ConfigurationResponse(StrictModel):
    environment_id: str
    component_versions: dict[str, str]
    corpus_manifest_sha256: str
    rule_catalog: tuple[dict[str, Any], ...]
    limits: tuple[dict[str, Any], ...]
    state_machine: tuple[dict[str, Any], ...]
    model_configurations: tuple[dict[str, Any], ...]
    settings: dict[str, Any]
    prohibited_integrations: tuple[dict[str, str], ...]
    kill_switch: KillSwitchResponse
    status: dict[str, str]


class AuditVerifyRequest(StrictModel):
    case_id: IdStr | None = None


class TevvRunRequest(StrictModel):
    scenario_ids: tuple[str, ...] = ()


class TevvResultView(StrictModel):
    scenario_id: str
    title: str
    category: str
    repetition: int
    status: str
    expected: dict[str, Any]
    actual: dict[str, Any]
    case_id: str | None
    trace_id: str
    defect_ids: tuple[str, ...]
    executed_at: datetime


class TevvRunResponse(StrictModel):
    tevv_run_id: str
    plan_version: str
    executor: str
    started_at: datetime
    completed_at: datetime | None
    component_versions: dict[str, str]
    summary: dict[str, Any]
    results: tuple[TevvResultView, ...]


class HealthResponse(StrictModel):
    status: str
    environment_id: str
    checks: dict[str, str] = Field(default_factory=dict)
