"""The frozen V1 rule catalog (Section 11.1).

Each rule is a pure function of :class:`RuleContext`. Precedence rank is explicit: a lower
rank outranks a higher one, and ``AUTH-001``/``KILL-001`` sit at the top so that authority
and the emergency stop can never be outvoted by a downstream result.
"""

from __future__ import annotations

from app.domain.enums import CaseState, IdentityStatus, RuleEffect, SupportState
from app.domain.limits import (
    CONCURRENT_CASES_MAX,
    EXCERPT_MAX_CHARS,
    EXCERPTS_USED_MAX,
    MODEL_CALLS_MAX,
    MODEL_OUTPUT_MAX_CHARS,
    QUESTION_MAX_CHARS,
    RATIONALE_MIN_CHARS,
    RETRIEVAL_CANDIDATE_MAX,
    SAME_ENDPOINT_RETRY_MAX,
    SOURCE_PLAN_MAX,
    TOTAL_EVIDENCE_CONTEXT_MAX_CHARS,
    CASE_WALL_CLOCK_SECONDS,
)
from app.domain.reason_codes import ReasonCode
from app.domain.versions import RULE_CATALOG_VERSION
from app.rules.framework import RuleContext, RuleOutcomeSpec, rule

V = "1.0.0"

ALL_STATES = tuple(CaseState)
PRE_HUMAN_STATES = (
    CaseState.AUTHORIZATION_PREFLIGHT,
    CaseState.ACTOR_AND_SESSION_VERIFICATION,
    CaseState.REQUEST_NORMALIZATION,
    CaseState.USE_CASE_AND_RISK_SCOPE,
    CaseState.EVIDENCE_PLAN,
    CaseState.SOURCE_ELIGIBILITY,
    CaseState.READ_ONLY_RETRIEVAL_AND_ISOLATION,
    CaseState.EVIDENCE_SUFFICIENCY,
    CaseState.BOUNDED_DRAFT,
    CaseState.INDEPENDENT_VERIFICATION,
    CaseState.DETERMINISTIC_GOVERNANCE,
)


# --------------------------------------------------------------------------------------
# KILL-001 - emergency stop. Highest precedence: nothing proceeds while it is active.
# --------------------------------------------------------------------------------------
@rule(
    "KILL-001",
    version=V,
    precedence=0,
    states=(
        *PRE_HUMAN_STATES,
        CaseState.REVIEWER_AUTHORITY_AND_SOD,
        CaseState.DISPOSITION_BINDING,
    ),
    purpose="Stop intake, processing and review disposition while the kill switch is active.",
)
def kill_001(context: RuleContext) -> RuleOutcomeSpec:
    if context.kill_switch_active:
        return RuleOutcomeSpec.failed(
            ReasonCode.EMERGENCY_STOP_ACTIVE,
            detail="Administrator emergency stop is active.",
        )
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# PATH-001 - no operational connector may exist or be reachable.
# --------------------------------------------------------------------------------------
@rule(
    "PATH-001",
    version=V,
    precedence=1,
    states=ALL_STATES,
    purpose="Confirm that no operational connector or action endpoint is configured or attempted.",
)
def path_001(context: RuleContext) -> RuleOutcomeSpec:
    if context.configured_action_endpoints:
        return RuleOutcomeSpec.failed(
            ReasonCode.PROHIBITED_ACTION_PATH_DETECTED,
            input_refs=context.configured_action_endpoints,
            detail="An operational action endpoint is configured; V1 permits none.",
        )
    if context.attempted_action_path:
        return RuleOutcomeSpec.failed(
            ReasonCode.PROHIBITED_ACTION_PATH_DETECTED,
            input_refs=(context.attempted_action_path,),
            detail="An operational action path was attempted and blocked.",
        )
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# AUTH-001 - exact synthetic authorization fixture.
# --------------------------------------------------------------------------------------
@rule(
    "AUTH-001",
    version=V,
    precedence=2,
    states=(CaseState.AUTHORIZATION_PREFLIGHT,),
    purpose="Validate the exact synthetic authorization fixture, version, environment, data and role scope.",
)
def auth_001(context: RuleContext) -> RuleOutcomeSpec:
    authorization = context.authorization
    if authorization is None:
        return RuleOutcomeSpec.failed(ReasonCode.AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE)
    if not authorization.is_current(context.evaluated_at):
        return RuleOutcomeSpec.failed(
            ReasonCode.AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE,
            input_refs=(authorization.authorization_id,),
            detail="Authorization fixture is revoked or outside its demo period.",
        )
    if context.manifest_sha256 and authorization.source_manifest_sha256 != context.manifest_sha256:
        return RuleOutcomeSpec.failed(
            ReasonCode.MANIFEST_HASH_MISMATCH,
            input_refs=(authorization.authorization_id,),
            detail="The frozen corpus manifest hash is not the one this authorization admits.",
        )
    if context.contract and authorization.use_case_contract_id != context.contract.use_case_contract_id:
        return RuleOutcomeSpec.failed(
            ReasonCode.AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE,
            input_refs=(authorization.authorization_id,),
            detail="The use case contract is not the one this authorization admits.",
        )
    if context.identity and context.identity.role_id not in authorization.allowed_role_ids:
        return RuleOutcomeSpec.failed(
            ReasonCode.AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE,
            input_refs=(context.identity.role_id,),
            detail="The acting role is outside the authorized role set.",
        )
    return RuleOutcomeSpec.passed(input_refs=(authorization.authorization_id,))


# --------------------------------------------------------------------------------------
# ID-001 - server session, expiry, revocation and role.
# --------------------------------------------------------------------------------------
@rule(
    "ID-001",
    version=V,
    precedence=3,
    states=(CaseState.ACTOR_AND_SESSION_VERIFICATION,),
    purpose="Validate the server session, its expiry, revocation state and role. Denies without disclosing case content.",
)
def id_001(context: RuleContext) -> RuleOutcomeSpec:
    identity = context.identity
    if identity is None:
        return RuleOutcomeSpec.failed(
            ReasonCode.REQUESTER_OR_SESSION_INVALID,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
        )
    if identity.status is not IdentityStatus.ACTIVE:
        return RuleOutcomeSpec.failed(
            ReasonCode.REQUESTER_OR_SESSION_INVALID,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="Identity is expired, revoked or unknown.",
        )
    if not identity.is_valid_at(context.evaluated_at):
        return RuleOutcomeSpec.failed(
            ReasonCode.REQUESTER_OR_SESSION_INVALID,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="Session is outside its validity window.",
        )
    if context.authorization and identity.business_scope_id != context.authorization.business_scope_id:
        return RuleOutcomeSpec.failed(
            ReasonCode.ACCESS_DENIED,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="Identity business scope does not match the authorized scope.",
        )
    return RuleOutcomeSpec.passed(input_refs=(identity.session_id,))


# --------------------------------------------------------------------------------------
# REQ-001 - one bounded question.
# --------------------------------------------------------------------------------------
@rule(
    "REQ-001",
    version=V,
    precedence=4,
    states=(CaseState.REQUEST_NORMALIZATION,),
    purpose="Enforce one bounded question, permitted purpose, length and synthetic classification.",
)
def req_001(context: RuleContext) -> RuleOutcomeSpec:
    contract = context.contract
    question = context.normalised_question
    if contract is None:
        return RuleOutcomeSpec.failed(ReasonCode.REQUEST_CONTRACT_INVALID)
    if not question.strip():
        return RuleOutcomeSpec.failed(
            ReasonCode.REQUEST_CONTRACT_INVALID, detail="Question is empty."
        )
    minimum = int(context.contract_extras.get("min_question_chars", 20))
    if len(question) < minimum:
        return RuleOutcomeSpec.failed(
            ReasonCode.REQUEST_CONTRACT_INVALID,
            detail="Question is shorter than the bounded minimum.",
        )
    if len(question) > min(contract.max_question_chars, QUESTION_MAX_CHARS):
        return RuleOutcomeSpec.failed(
            ReasonCode.REQUEST_LIMIT_EXCEEDED, detail="Question exceeds the frozen length limit."
        )
    if question.count("?") > 1:
        return RuleOutcomeSpec.failed(
            ReasonCode.REQUEST_CONTRACT_INVALID,
            detail="More than one question was submitted; V1 admits exactly one.",
        )
    lowered = question.casefold()
    markers = context.contract_extras.get("multi_question_markers", ())
    for marker in markers:
        if marker.casefold() in lowered:
            return RuleOutcomeSpec.failed(
                ReasonCode.REQUEST_CONTRACT_INVALID,
                input_refs=(marker,),
                detail="The request bundles multiple questions.",
            )
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# SCOPE-001 - excluded action-seeking scope.
# --------------------------------------------------------------------------------------
@rule(
    "SCOPE-001",
    version=V,
    precedence=5,
    states=(CaseState.USE_CASE_AND_RISK_SCOPE,),
    purpose="Block excluded action-seeking or high-impact scope terms.",
)
def scope_001(context: RuleContext) -> RuleOutcomeSpec:
    contract = context.contract
    if contract is None:
        return RuleOutcomeSpec.failed(ReasonCode.USE_CASE_EXCLUDED_OR_UNBOUNDED)
    lowered = context.normalised_question.casefold()
    hits = sorted({term for term in contract.excluded_scope_terms if term.casefold() in lowered})
    if hits:
        return RuleOutcomeSpec.failed(
            ReasonCode.USE_CASE_EXCLUDED_OR_UNBOUNDED,
            input_refs=tuple(hits),
            detail="The request seeks an excluded action or outcome.",
        )
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# SRC-001 - manifest membership, hash, lifecycle, use case, scope and access.
# --------------------------------------------------------------------------------------
@rule(
    "SRC-001",
    version=V,
    precedence=6,
    states=(CaseState.SOURCE_ELIGIBILITY,),
    purpose="Validate manifest membership, hash, lifecycle, use case, scope and access for each source.",
)
def src_001(context: RuleContext) -> RuleOutcomeSpec:
    if context.hash_mismatches:
        return RuleOutcomeSpec.failed(
            ReasonCode.MANIFEST_HASH_MISMATCH,
            input_refs=context.hash_mismatches,
            detail="A source file hash does not match the frozen manifest.",
        )
    if len(context.planned_sources) > SOURCE_PLAN_MAX:
        return RuleOutcomeSpec.failed(
            ReasonCode.SOURCE_LIMIT_EXCEEDED,
            detail=f"The evidence plan exceeds {SOURCE_PLAN_MAX} sources.",
        )
    if not context.eligible_sources:
        return RuleOutcomeSpec.failed(
            ReasonCode.SOURCE_ELIGIBILITY_FAILURE,
            input_refs=tuple(key for key, _ in context.excluded_sources),
            detail="No eligible, current, in-scope source remains after filtering.",
        )
    required_classes = set(context.contract.required_source_authority_classes) if context.contract else set()
    present_classes = {item.authority_class.value for item in context.eligible_sources}
    missing = sorted(required_classes - present_classes)
    if missing:
        return RuleOutcomeSpec.failed(
            ReasonCode.SOURCE_ELIGIBILITY_FAILURE,
            input_refs=tuple(missing),
            detail="A required source authority class is not eligible for this request.",
        )
    return RuleOutcomeSpec.passed(
        input_refs=tuple(item.source_key for item in context.eligible_sources)
    )


# --------------------------------------------------------------------------------------
# ISO-001 - quarantine and content isolation.
# --------------------------------------------------------------------------------------
@rule(
    "ISO-001",
    version=V,
    precedence=7,
    states=(CaseState.SOURCE_ELIGIBILITY, CaseState.READ_ONLY_RETRIEVAL_AND_ISOLATION),
    purpose="Treat injection or security indicators as a quarantine condition and log a security event.",
)
def iso_001(context: RuleContext) -> RuleOutcomeSpec:
    quarantined_and_admitted = sorted(
        {
            excerpt.source_id + "@" + excerpt.source_version
            for excerpt in context.excerpts
            if excerpt.instruction_like_flags
        }
    )
    if quarantined_and_admitted:
        return RuleOutcomeSpec.failed(
            ReasonCode.SOURCE_QUARANTINED,
            input_refs=tuple(quarantined_and_admitted),
            detail="Instruction-like content reached the admitted excerpt set.",
        )
    if context.quarantined_sources:
        # Quarantined sources were correctly excluded before retrieval. That is a pass with
        # a recorded reference, not a stop, unless the source was required.
        return RuleOutcomeSpec.passed(
            input_refs=context.quarantined_sources,
            detail="Quarantined sources were excluded before retrieval.",
        )
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# EVD-001 - required source classes and sufficiency.
# --------------------------------------------------------------------------------------
@rule(
    "EVD-001",
    version=V,
    precedence=8,
    states=(CaseState.EVIDENCE_SUFFICIENCY,),
    purpose="Ensure required source classes and date/scope criteria exist, and that no material conflict is unresolved.",
)
def evd_001(context: RuleContext) -> RuleOutcomeSpec:
    if not context.excerpts:
        return RuleOutcomeSpec.failed(
            ReasonCode.EVIDENCE_INSUFFICIENT_OR_CONFLICTED,
            detail="No admitted evidence excerpt is available.",
        )
    if context.triggered_conflicts:
        return RuleOutcomeSpec.failed(
            ReasonCode.EVIDENCE_INSUFFICIENT_OR_CONFLICTED,
            input_refs=tuple(conflict.conflict_id for conflict in context.triggered_conflicts),
            detail="A declared material conflict between active sources applies to this request.",
        )
    required_classes = set(context.contract.required_source_authority_classes) if context.contract else set()
    admitted_keys = {f"{excerpt.source_id}@{excerpt.source_version}" for excerpt in context.excerpts}
    admitted_classes = {
        item.authority_class.value
        for item in context.eligible_sources
        if item.source_key in admitted_keys
    }
    missing = sorted(required_classes - admitted_classes)
    if missing:
        return RuleOutcomeSpec.failed(
            ReasonCode.EVIDENCE_INSUFFICIENT_OR_CONFLICTED,
            input_refs=tuple(missing),
            detail="No excerpt from a required source authority class was admitted.",
        )
    return RuleOutcomeSpec.passed(input_refs=tuple(sorted(admitted_keys)))


# --------------------------------------------------------------------------------------
# CLM-001 - material claim support and exact citation existence.
# --------------------------------------------------------------------------------------
@rule(
    "CLM-001",
    version=V,
    precedence=9,
    states=(CaseState.INDEPENDENT_VERIFICATION,),
    purpose="Enforce material claim support and the existence of exact citations.",
)
def clm_001(context: RuleContext) -> RuleOutcomeSpec:
    if context.material_claim_failures:
        return RuleOutcomeSpec.failed(
            ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
            input_refs=context.material_claim_failures,
            detail="At least one material claim is unsupported, conflicted or has no exact citation.",
        )
    if context.verification is None:
        return RuleOutcomeSpec.failed(
            ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
            detail="No independent verification result is available.",
        )
    admitted = {excerpt.excerpt_id for excerpt in context.excerpts}
    fabricated = sorted(
        {
            evidence_id
            for claim in context.verification.verified_claims
            for evidence_id in claim.evidence_ids
            if evidence_id not in admitted
        }
    )
    if fabricated:
        return RuleOutcomeSpec.failed(
            ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
            input_refs=tuple(fabricated),
            detail="A citation references an excerpt that was never admitted.",
        )
    conflicted = sorted(
        {
            claim.claim_ref
            for claim in context.verification.verified_claims
            if claim.support_state is SupportState.CONFLICTED
        }
    )
    if conflicted:
        return RuleOutcomeSpec.failed(
            ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
            input_refs=tuple(conflicted),
            detail="A verified claim is conflicted.",
        )
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# LIM-001 - resource limits.
# --------------------------------------------------------------------------------------
@rule(
    "LIM-001",
    version=V,
    precedence=10,
    states=ALL_STATES,
    purpose="Enforce request, context, call, retry, output, time and concurrency limits without expanded retry.",
)
def lim_001(context: RuleContext) -> RuleOutcomeSpec:
    checks: tuple[tuple[bool, ReasonCode, str], ...] = (
        (
            len(context.normalised_question) > QUESTION_MAX_CHARS,
            ReasonCode.REQUEST_LIMIT_EXCEEDED,
            "question length",
        ),
        (
            len(context.planned_sources) > SOURCE_PLAN_MAX,
            ReasonCode.SOURCE_LIMIT_EXCEEDED,
            "sources in plan",
        ),
        (
            context.retrieval_candidate_count > RETRIEVAL_CANDIDATE_MAX,
            ReasonCode.RETRIEVAL_LIMIT_EXCEEDED,
            "retrieval candidates",
        ),
        (
            len(context.excerpts) > EXCERPTS_USED_MAX,
            ReasonCode.EXCERPT_LIMIT_EXCEEDED,
            "excerpts used",
        ),
        (
            any(len(excerpt.text) > EXCERPT_MAX_CHARS for excerpt in context.excerpts),
            ReasonCode.EXCERPT_SIZE_LIMIT_EXCEEDED,
            "excerpt size",
        ),
        (
            context.total_context_chars > TOTAL_EVIDENCE_CONTEXT_MAX_CHARS,
            ReasonCode.CONTEXT_LIMIT_EXCEEDED,
            "total evidence context",
        ),
        (
            context.model_calls_used > MODEL_CALLS_MAX,
            ReasonCode.MODEL_CALL_LIMIT_EXCEEDED,
            "model calls",
        ),
        (
            context.retries_used > SAME_ENDPOINT_RETRY_MAX,
            ReasonCode.RETRY_LIMIT_EXCEEDED,
            "same-endpoint retries",
        ),
        (
            context.max_model_output_chars > MODEL_OUTPUT_MAX_CHARS,
            ReasonCode.MODEL_OUTPUT_LIMIT_EXCEEDED,
            "model output",
        ),
        (
            context.elapsed_seconds > CASE_WALL_CLOCK_SECONDS,
            ReasonCode.CASE_WALL_CLOCK_LIMIT_EXCEEDED,
            "case wall clock",
        ),
        (
            context.concurrent_cases > CONCURRENT_CASES_MAX,
            ReasonCode.CONCURRENCY_LIMIT_EXCEEDED,
            "concurrent cases",
        ),
    )
    for breached, reason, label in checks:
        if breached:
            return RuleOutcomeSpec.failed(reason, input_refs=(label,), detail=f"{label} over limit")
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# FSM-001 - declared transitions only.
# --------------------------------------------------------------------------------------
@rule(
    "FSM-001",
    version=V,
    precedence=11,
    states=ALL_STATES,
    purpose="Permit only declared state transitions in order; reject and log any other edge.",
)
def fsm_001(context: RuleContext) -> RuleOutcomeSpec:
    # The engine calls ``assert_transition`` before a state is entered; this rule records
    # the deterministic evidence that the entered state was reached through a declared edge.
    return RuleOutcomeSpec.passed(input_refs=(context.state.value,))


# --------------------------------------------------------------------------------------
# PKT-001 - packet contract.
# --------------------------------------------------------------------------------------
@rule(
    "PKT-001",
    version=V,
    precedence=12,
    states=(CaseState.STRUCTURAL_AND_SEMANTIC_VALIDATION,),
    purpose="Validate packet required sections, fixed notices, references, versions and timestamps.",
)
def pkt_001(context: RuleContext) -> RuleOutcomeSpec:
    if context.packet_payload is None:
        return RuleOutcomeSpec.failed(
            ReasonCode.PACKET_CONTRACT_FAILURE, detail="No packet payload was assembled."
        )
    if context.packet_validation_errors:
        return RuleOutcomeSpec.failed(
            ReasonCode.PACKET_CONTRACT_FAILURE,
            input_refs=context.packet_validation_errors[:8],
            detail="Packet semantic validation reported failures.",
        )
    return RuleOutcomeSpec.passed()


# --------------------------------------------------------------------------------------
# AUD-001 - distinct confirmed critical audit events.
# --------------------------------------------------------------------------------------
@rule(
    "AUD-001",
    version=V,
    precedence=13,
    states=(CaseState.PACKET_PRE_ISSUANCE_AUDIT, CaseState.DISPOSITION_CLOSURE_AUDIT),
    purpose="Enforce distinct confirmed packet pre-issuance and disposition closure audit events.",
)
def aud_001(context: RuleContext) -> RuleOutcomeSpec:
    if context.state is CaseState.PACKET_PRE_ISSUANCE_AUDIT:
        if not context.confirmed_pre_issuance_event_id:
            return RuleOutcomeSpec.failed(
                ReasonCode.CRITICAL_AUDIT_FAILURE,
                detail="No confirmed packet pre-issuance audit event exists.",
            )
        return RuleOutcomeSpec.passed(input_refs=(context.confirmed_pre_issuance_event_id,))

    if not context.confirmed_closure_event_id:
        return RuleOutcomeSpec.failed(
            ReasonCode.CRITICAL_AUDIT_FAILURE,
            detail="No confirmed disposition closure audit event exists.",
        )
    if context.confirmed_closure_event_id == context.confirmed_pre_issuance_event_id:
        return RuleOutcomeSpec.failed(
            ReasonCode.CRITICAL_AUDIT_FAILURE,
            detail="Closure must be a distinct, later audit event than pre-issuance.",
        )
    return RuleOutcomeSpec.passed(
        input_refs=(
            str(context.confirmed_pre_issuance_event_id),
            context.confirmed_closure_event_id,
        )
    )


# --------------------------------------------------------------------------------------
# SOD-001 - reviewer authority and separation of duties.
# --------------------------------------------------------------------------------------
@rule(
    "SOD-001",
    version=V,
    precedence=14,
    states=(CaseState.REVIEWER_AUTHORITY_AND_SOD, CaseState.DISPOSITION_BINDING),
    purpose="Reject self-review, incompatible role, wrong scope and expired or revoked reviewers.",
)
def sod_001(context: RuleContext) -> RuleOutcomeSpec:
    reviewer = context.reviewer_identity_id
    if not reviewer:
        return RuleOutcomeSpec.failed(
            ReasonCode.REVIEWER_AUTHORITY_INVALID,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="No reviewer identity was reverified.",
        )
    if context.reviewer_status != IdentityStatus.ACTIVE.value:
        return RuleOutcomeSpec.failed(
            ReasonCode.REVIEWER_AUTHORITY_INVALID,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="Reviewer identity is expired, revoked or unknown.",
        )
    if context.reviewer_role_id != "ROLE_SYNTHETIC_REVIEWER_V1":
        return RuleOutcomeSpec.failed(
            ReasonCode.REVIEWER_AUTHORITY_INVALID,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="The acting role is not an authorised reviewer role.",
        )
    if context.authorization and context.reviewer_scope_id != context.authorization.business_scope_id:
        return RuleOutcomeSpec.failed(
            ReasonCode.ACCESS_DENIED,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="Reviewer business scope does not match the case scope.",
        )
    if context.requester_identity_id and reviewer == context.requester_identity_id:
        return RuleOutcomeSpec.failed(
            ReasonCode.SEPARATION_OF_DUTIES_VIOLATION,
            effect=RuleEffect.DENY_WITHOUT_DISCLOSURE,
            detail="An identity cannot review the case it requested.",
        )
    if context.state is CaseState.DISPOSITION_BINDING:
        rationale = (context.disposition_rationale or "").strip()
        if len(rationale) < RATIONALE_MIN_CHARS:
            return RuleOutcomeSpec.failed(
                ReasonCode.DISPOSITION_RATIONALE_REQUIRED,
                detail="A substantive human rationale is required before a disposition binds.",
            )
    return RuleOutcomeSpec.passed(input_refs=(reviewer,))


def catalog_payload() -> list[dict[str, object]]:
    """Machine-readable rule catalog for documentation and the admin endpoint."""
    from app.rules.framework import REGISTRY

    return [
        {
            "rule_id": rule_def.rule_id,
            "rule_version": rule_def.rule_version,
            "catalog_version": RULE_CATALOG_VERSION,
            "precedence_rank": rule_def.precedence_rank,
            "purpose": rule_def.purpose,
            "evaluated_in_states": sorted(state.value for state in rule_def.states),
        }
        for rule_def in REGISTRY.all()
    ]
