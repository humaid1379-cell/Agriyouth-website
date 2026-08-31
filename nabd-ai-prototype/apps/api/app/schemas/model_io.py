"""Model gateway contracts.

The draft and verifier schemas are closed. They contain no field through which a model can
select a route, assert authority, waive a rule, request a tool or name a source that was
not admitted by the deterministic evidence stage.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from app.domain.enums import (
    AuthorizationStatus,
    Materiality,
    ModelMode,
    ModelTaskRole,
    OperationalStatus,
    StatusEvidence,
    SupportState,
)
from app.domain.limits import (
    DRAFT_INPUT_MAX_CHARS,
    MODEL_OUTPUT_MAX_CHARS,
    PER_CALL_TIMEOUT_SECONDS,
    SAME_ENDPOINT_RETRY_MAX,
    VERIFIER_INPUT_MAX_CHARS,
)
from app.schemas.base import HashStr, IdStr, StrictModel, VersionedRecord, VersionStr
from app.schemas.evidence import EvidenceExcerpt

#: Substrings that indicate a model tried to request a tool, call a URL or assert
#: authority. Their presence in a response is a boundary failure, not a warning.
PROHIBITED_OUTPUT_MARKERS: tuple[str, ...] = (
    "tool_call",
    "function_call",
    "http://",
    "https://",
    "webhook",
    "send_email",
    "approve_action",
    "execute(",
    "os.system",
)


class ModelConfiguration(VersionedRecord):
    """Exactly one pinned configuration is active per run. Any material change is a new ID."""

    model_configuration_id: IdStr
    provider_runtime: str
    model_revision: str
    endpoint_or_artifact_hash: str
    task_role: ModelTaskRole
    prompt_version: VersionStr
    output_schema_id: IdStr
    temperature_milli: Annotated[int, Field(ge=0, le=2000)] = 0
    top_p_milli: Annotated[int, Field(ge=0, le=1000)] = 1000
    seed: int = 0
    context_limit_chars: Annotated[int, Field(ge=1)]
    output_limit_chars: Annotated[int, Field(ge=1, le=MODEL_OUTPUT_MAX_CHARS)]
    timeout_seconds: Annotated[int, Field(ge=1, le=PER_CALL_TIMEOUT_SECONDS)] = (
        PER_CALL_TIMEOUT_SECONDS
    )
    max_same_endpoint_retries: Annotated[int, Field(ge=0, le=SAME_ENDPOINT_RETRY_MAX)] = (
        SAME_ENDPOINT_RETRY_MAX
    )
    tool_calling_enabled: Literal[False] = False
    fallback_enabled: Literal[False] = False
    data_handling_note: str
    evaluation_version: VersionStr
    effective_from: datetime
    effective_to: datetime | None = None
    revoked: bool = False
    mode: ModelMode = ModelMode.MOCK
    built: StatusEvidence = StatusEvidence.NOT_EVIDENCED
    integration: StatusEvidence = StatusEvidence.NOT_EVIDENCED
    operational: OperationalStatus = OperationalStatus.NOT_EVIDENCED
    authorization: AuthorizationStatus = AuthorizationStatus.NOT_GRANTED

    def is_current(self, at: datetime) -> bool:
        if self.revoked or at < self.effective_from:
            return False
        return self.effective_to is None or at <= self.effective_to


class DraftRequest(StrictModel):
    case_id: IdStr
    normalised_question: Annotated[str, Field(min_length=1)]
    permitted_purpose: IdStr
    output_schema_id: IdStr
    prompt_version: VersionStr
    excerpts: tuple[EvidenceExcerpt, ...] = Field(min_length=1)
    rendered_input: Annotated[str, Field(max_length=DRAFT_INPUT_MAX_CHARS)]

    @property
    def admitted_excerpt_ids(self) -> frozenset[str]:
        return frozenset(excerpt.excerpt_id for excerpt in self.excerpts)


class DraftClaim(StrictModel):
    """A candidate claim. It carries proposed evidence IDs only, never a verdict."""

    claim_ref: Annotated[str, Field(pattern=r"^C[0-9]{2}$")]
    statement: Annotated[str, Field(min_length=1, max_length=1000)]
    materiality: Materiality
    proposed_evidence_ids: tuple[IdStr, ...] = Field(min_length=1, max_length=8)


class DraftResponse(StrictModel):
    claims: tuple[DraftClaim, ...] = Field(min_length=1, max_length=12)
    assumptions: tuple[Annotated[str, Field(max_length=500)], ...] = Field(max_length=8)
    unresolved_points: tuple[Annotated[str, Field(max_length=500)], ...] = Field(max_length=8)
    draft_summary: Annotated[str, Field(min_length=1, max_length=2000)]

    @model_validator(mode="after")
    def _unique_claim_refs(self) -> DraftResponse:
        refs = [claim.claim_ref for claim in self.claims]
        if len(set(refs)) != len(refs):
            raise ValueError("claim_ref values must be unique within a draft")
        return self


class VerificationRequest(StrictModel):
    case_id: IdStr
    output_schema_id: IdStr
    prompt_version: VersionStr
    draft_claims: tuple[DraftClaim, ...] = Field(min_length=1)
    excerpts: tuple[EvidenceExcerpt, ...] = Field(min_length=1)
    rendered_input: Annotated[str, Field(max_length=VERIFIER_INPUT_MAX_CHARS)]


class SupportSpan(StrictModel):
    excerpt_id: IdStr
    quote_start: Annotated[int, Field(ge=0)]
    quote_end: Annotated[int, Field(ge=0)]
    quoted_text: Annotated[str, Field(min_length=1, max_length=600)]

    @model_validator(mode="after")
    def _ordered(self) -> SupportSpan:
        if self.quote_end <= self.quote_start:
            raise ValueError("quote_end must be greater than quote_start")
        return self


class VerifiedClaim(StrictModel):
    claim_ref: Annotated[str, Field(pattern=r"^C[0-9]{2}$")]
    support_state: SupportState
    evidence_ids: tuple[IdStr, ...] = Field(max_length=8)
    support_spans: tuple[SupportSpan, ...] = Field(max_length=8)
    conflict_ids: tuple[IdStr, ...] = Field(max_length=8)
    qualification: Annotated[str, Field(max_length=500)] = ""
    verification_note: Annotated[str, Field(max_length=800)] = ""

    @model_validator(mode="after")
    def _support_requires_evidence(self) -> VerifiedClaim:
        if self.support_state is SupportState.SUPPORTED and not self.evidence_ids:
            raise ValueError("a SUPPORTED claim must cite at least one evidence id")
        span_ids = {span.excerpt_id for span in self.support_spans}
        if not span_ids.issubset(set(self.evidence_ids)):
            raise ValueError("support spans must reference cited evidence ids")
        return self


class VerificationResponse(StrictModel):
    verified_claims: tuple[VerifiedClaim, ...] = Field(min_length=1, max_length=12)
    verifier_notes: Annotated[str, Field(max_length=2000)] = ""

    @model_validator(mode="after")
    def _unique_refs(self) -> VerificationResponse:
        refs = [claim.claim_ref for claim in self.verified_claims]
        if len(set(refs)) != len(refs):
            raise ValueError("claim_ref values must be unique within a verification")
        return self


class ModelRunRecord(VersionedRecord):
    model_run_id: IdStr
    case_id: IdStr
    model_configuration_id: IdStr
    task_role: ModelTaskRole
    call_index: Annotated[int, Field(ge=1, le=2)]
    retry_count: Annotated[int, Field(ge=0, le=SAME_ENDPOINT_RETRY_MAX)]
    input_chars: Annotated[int, Field(ge=0)]
    output_chars: Annotated[int, Field(ge=0)]
    input_sha256: HashStr
    output_sha256: HashStr
    duration_ms: Annotated[int, Field(ge=0)]
    succeeded: bool
    reason_code: str | None = None
    mode: ModelMode

    @field_validator("reason_code")
    @classmethod
    def _reason_present_on_failure(cls, value: str | None) -> str | None:
        return value
