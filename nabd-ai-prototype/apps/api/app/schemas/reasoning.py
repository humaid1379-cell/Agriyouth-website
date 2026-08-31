"""Claim ledger, deterministic rule results, uncertainty and risk objects."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import Field, model_validator

from app.domain.enums import (
    Materiality,
    RiskLevel,
    RuleEffect,
    RuleOutcome,
    Severity,
    SupportState,
    UncertaintyKind,
)
from app.schemas.base import IdStr, StrictModel, VersionedRecord, VersionStr
from app.schemas.model_io import SupportSpan


class ClaimEvidenceLink(StrictModel):
    excerpt_id: IdStr
    source_id: IdStr
    source_version: VersionStr
    page_number: Annotated[int, Field(ge=1)]
    section_heading: str
    char_start: Annotated[int, Field(ge=0)]
    char_end: Annotated[int, Field(ge=0)]
    quoted_text: str
    quote_verified: bool


class GeneratedClaim(VersionedRecord):
    """A drafted claim after independent verification and deterministic binding."""

    claim_id: IdStr
    case_id: IdStr
    claim_ref: Annotated[str, Field(pattern=r"^C[0-9]{2}$")]
    statement: Annotated[str, Field(min_length=1, max_length=1000)]
    materiality: Materiality
    support_state: SupportState
    evidence_links: tuple[ClaimEvidenceLink, ...]
    support_spans: tuple[SupportSpan, ...] = ()
    conflict_ids: tuple[IdStr, ...] = ()
    qualification: str = ""
    verification_note: str = ""
    draft_model_run_id: IdStr
    verifier_model_run_id: IdStr

    @property
    def is_blocking(self) -> bool:
        """A material claim that is not fully supported blocks packet issuance."""
        return self.materiality is Materiality.MATERIAL and self.support_state is not (
            SupportState.SUPPORTED
        )


class DeterministicResult(VersionedRecord):
    rule_id: IdStr
    rule_version: VersionStr
    case_id: IdStr
    input_refs: tuple[str, ...]
    outcome: RuleOutcome
    reason_code: str
    effect: RuleEffect
    precedence_rank: Annotated[int, Field(ge=0)]
    evaluated_at: datetime
    detail: str = ""

    @property
    def is_mandatory_stop(self) -> bool:
        return self.outcome is RuleOutcome.FAIL and self.effect in {
            RuleEffect.MANDATORY_STOP,
            RuleEffect.DENY_WITHOUT_DISCLOSURE,
        }


class UncertaintyRecord(VersionedRecord):
    uncertainty_id: IdStr
    case_id: IdStr
    kind: UncertaintyKind
    description_en: str
    description_ar: str = ""
    affected_claim_refs: tuple[str, ...] = ()
    affected_source_ids: tuple[IdStr, ...] = ()
    increases_risk: bool = True


class RiskFactor(StrictModel):
    factor_id: IdStr
    label_en: str
    label_ar: str = ""
    level: RiskLevel
    rationale: str


class RiskProfile(StrictModel):
    """Dominant-factor risk. ``CRITICAL`` and ``UNKNOWN`` are never averaged down."""

    factors: tuple[RiskFactor, ...] = Field(min_length=1)
    dominant_factor_id: IdStr
    inherent_risk: RiskLevel
    reviewer_seniority_required: str
    review_depth_required: str
    method: str = "dominant-factor-v1"

    @model_validator(mode="after")
    def _dominant_is_present(self) -> RiskProfile:
        if self.dominant_factor_id not in {factor.factor_id for factor in self.factors}:
            raise ValueError("dominant_factor_id must reference a listed factor")
        return self


class DefectRecord(VersionedRecord):
    defect_id: IdStr
    severity: Severity
    reported_at: datetime
    reporter: str
    affected_versions: tuple[VersionStr, ...]
    summary: str
    reproduction: str
    containment: str = ""
    owner: str = ""
    correction: str = ""
    test_refs: tuple[str, ...] = ()
    retest_refs: tuple[str, ...] = ()
    status: str = "OPEN"
