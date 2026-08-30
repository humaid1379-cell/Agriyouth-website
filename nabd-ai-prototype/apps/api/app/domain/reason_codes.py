"""Closed reason-code vocabulary.

Every stop, denial and limit breach in the prototype resolves to exactly one code from
this module. Free-text messages are display sugar; the code is the governed value.
"""

from __future__ import annotations

from enum import StrEnum

from app.domain.enums import CaseState


class ReasonCode(StrEnum):
    # -- Workflow stage failures (Section 11.2) -------------------------------------
    AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE = "AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE"
    REQUESTER_OR_SESSION_INVALID = "REQUESTER_OR_SESSION_INVALID"
    REQUEST_CONTRACT_INVALID = "REQUEST_CONTRACT_INVALID"
    USE_CASE_EXCLUDED_OR_UNBOUNDED = "USE_CASE_EXCLUDED_OR_UNBOUNDED"
    EVIDENCE_REQUIREMENT_UNRESOLVED = "EVIDENCE_REQUIREMENT_UNRESOLVED"
    SOURCE_ELIGIBILITY_FAILURE = "SOURCE_ELIGIBILITY_FAILURE"
    RETRIEVAL_OR_ISOLATION_FAILURE = "RETRIEVAL_OR_ISOLATION_FAILURE"
    EVIDENCE_INSUFFICIENT_OR_CONFLICTED = "EVIDENCE_INSUFFICIENT_OR_CONFLICTED"
    MODEL_BOUNDARY_OR_SCHEMA_FAILURE = "MODEL_BOUNDARY_OR_SCHEMA_FAILURE"
    MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED = "MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED"
    DETERMINISTIC_GOVERNANCE_FAILURE = "DETERMINISTIC_GOVERNANCE_FAILURE"
    ROUTE_INVARIANT_FAILURE = "ROUTE_INVARIANT_FAILURE"
    PACKET_ASSEMBLY_FAILURE = "PACKET_ASSEMBLY_FAILURE"
    PACKET_CONTRACT_FAILURE = "PACKET_CONTRACT_FAILURE"
    CRITICAL_AUDIT_FAILURE = "CRITICAL_AUDIT_FAILURE"

    # -- Numeric limits (Section 15.3) ---------------------------------------------
    REQUEST_LIMIT_EXCEEDED = "REQUEST_LIMIT_EXCEEDED"
    SOURCE_LIMIT_EXCEEDED = "SOURCE_LIMIT_EXCEEDED"
    RETRIEVAL_LIMIT_EXCEEDED = "RETRIEVAL_LIMIT_EXCEEDED"
    EXCERPT_LIMIT_EXCEEDED = "EXCERPT_LIMIT_EXCEEDED"
    EXCERPT_SIZE_LIMIT_EXCEEDED = "EXCERPT_SIZE_LIMIT_EXCEEDED"
    CONTEXT_LIMIT_EXCEEDED = "CONTEXT_LIMIT_EXCEEDED"
    MODEL_CALL_LIMIT_EXCEEDED = "MODEL_CALL_LIMIT_EXCEEDED"
    RETRY_LIMIT_EXCEEDED = "RETRY_LIMIT_EXCEEDED"
    MODEL_OUTPUT_LIMIT_EXCEEDED = "MODEL_OUTPUT_LIMIT_EXCEEDED"
    CASE_WALL_CLOCK_LIMIT_EXCEEDED = "CASE_WALL_CLOCK_LIMIT_EXCEEDED"
    CONCURRENCY_LIMIT_EXCEEDED = "CONCURRENCY_LIMIT_EXCEEDED"
    EXPORT_RATE_LIMIT_EXCEEDED = "EXPORT_RATE_LIMIT_EXCEEDED"

    # -- Control, authority and safety ---------------------------------------------
    EMERGENCY_STOP_ACTIVE = "EMERGENCY_STOP_ACTIVE"
    ILLEGAL_STATE_TRANSITION = "ILLEGAL_STATE_TRANSITION"
    PROHIBITED_ACTION_PATH_DETECTED = "PROHIBITED_ACTION_PATH_DETECTED"
    SEPARATION_OF_DUTIES_VIOLATION = "SEPARATION_OF_DUTIES_VIOLATION"
    REVIEWER_AUTHORITY_INVALID = "REVIEWER_AUTHORITY_INVALID"
    DISPOSITION_RATIONALE_REQUIRED = "DISPOSITION_RATIONALE_REQUIRED"
    DISPOSITION_ALREADY_FINAL = "DISPOSITION_ALREADY_FINAL"
    PACKET_NOT_AVAILABLE = "PACKET_NOT_AVAILABLE"
    ACCESS_DENIED = "ACCESS_DENIED"
    SOURCE_QUARANTINED = "SOURCE_QUARANTINED"
    MANIFEST_HASH_MISMATCH = "MANIFEST_HASH_MISMATCH"
    MODEL_CONFIGURATION_MISMATCH = "MODEL_CONFIGURATION_MISMATCH"
    MODEL_FALLBACK_ATTEMPTED = "MODEL_FALLBACK_ATTEMPTED"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    MODEL_REFUSAL = "MODEL_REFUSAL"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    AUDIT_CHAIN_DIVERGENCE = "AUDIT_CHAIN_DIVERGENCE"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_CONTROL_FAILURE = "INTERNAL_CONTROL_FAILURE"


#: Human-readable, non-leaking message per code. Messages never contain case content,
#: prompts, credentials, hidden settings or source text.
REASON_MESSAGES: dict[ReasonCode, str] = {
    ReasonCode.AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE: (
        "The synthetic prototype authorization fixture is absent, expired or out of scope."
    ),
    ReasonCode.REQUESTER_OR_SESSION_INVALID: (
        "The demo session or role could not be verified for this action."
    ),
    ReasonCode.REQUEST_CONTRACT_INVALID: (
        "The request is not one bounded, in-contract synthetic policy or SOP question."
    ),
    ReasonCode.USE_CASE_EXCLUDED_OR_UNBOUNDED: (
        "The request seeks an excluded action or falls outside the bounded V1 use case."
    ),
    ReasonCode.EVIDENCE_REQUIREMENT_UNRESOLVED: (
        "Required evidence classes for this request could not be determined."
    ),
    ReasonCode.SOURCE_ELIGIBILITY_FAILURE: (
        "A required source is not eligible, current or in scope under the frozen manifest."
    ),
    ReasonCode.RETRIEVAL_OR_ISOLATION_FAILURE: (
        "Controlled retrieval or content isolation did not complete safely."
    ),
    ReasonCode.EVIDENCE_INSUFFICIENT_OR_CONFLICTED: (
        "Admitted evidence is insufficient, or a material conflict between active sources exists."
    ),
    ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE: (
        "A model response breached its boundary, schema, limit or timeout contract."
    ),
    ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED: (
        "A material claim is unsupported or conflicted under the frozen V1 rules."
    ),
    ReasonCode.DETERMINISTIC_GOVERNANCE_FAILURE: (
        "A deterministic governance rule failed or could not be evaluated."
    ),
    ReasonCode.ROUTE_INVARIANT_FAILURE: "The selected route violated a V1 route invariant.",
    ReasonCode.PACKET_ASSEMBLY_FAILURE: "The Decision Readiness Packet could not be assembled.",
    ReasonCode.PACKET_CONTRACT_FAILURE: (
        "The packet failed structural or semantic validation and cannot be displayed."
    ),
    ReasonCode.CRITICAL_AUDIT_FAILURE: (
        "A required confirmed audit event is missing, so display or closure is withheld."
    ),
    ReasonCode.REQUEST_LIMIT_EXCEEDED: "The request exceeds the frozen question length limit.",
    ReasonCode.SOURCE_LIMIT_EXCEEDED: "The evidence plan exceeds the frozen source limit.",
    ReasonCode.RETRIEVAL_LIMIT_EXCEEDED: "Retrieval exceeded the frozen candidate limit.",
    ReasonCode.EXCERPT_LIMIT_EXCEEDED: "The admitted excerpt count exceeds the frozen limit.",
    ReasonCode.EXCERPT_SIZE_LIMIT_EXCEEDED: "An excerpt exceeds the frozen character limit.",
    ReasonCode.CONTEXT_LIMIT_EXCEEDED: "Total evidence context exceeds the frozen limit.",
    ReasonCode.MODEL_CALL_LIMIT_EXCEEDED: "The two-call model budget for this case is exhausted.",
    ReasonCode.RETRY_LIMIT_EXCEEDED: "The same-endpoint retry budget for this case is exhausted.",
    ReasonCode.MODEL_OUTPUT_LIMIT_EXCEEDED: "A model response exceeds the frozen output limit.",
    ReasonCode.CASE_WALL_CLOCK_LIMIT_EXCEEDED: "Case processing exceeded the frozen time limit.",
    ReasonCode.CONCURRENCY_LIMIT_EXCEEDED: "The concurrent case limit is reached; retry later.",
    ReasonCode.EXPORT_RATE_LIMIT_EXCEEDED: "Packet export is rate limited for this version.",
    ReasonCode.EMERGENCY_STOP_ACTIVE: (
        "The administrator emergency stop is active; intake, processing and disposition are halted."
    ),
    ReasonCode.ILLEGAL_STATE_TRANSITION: "The requested workflow transition is not permitted.",
    ReasonCode.PROHIBITED_ACTION_PATH_DETECTED: (
        "A prohibited operational action path was detected and blocked."
    ),
    ReasonCode.SEPARATION_OF_DUTIES_VIOLATION: (
        "Separation of duties prevents this identity from reviewing this case."
    ),
    ReasonCode.REVIEWER_AUTHORITY_INVALID: (
        "Reviewer authority, role, scope or session validity could not be reverified."
    ),
    ReasonCode.DISPOSITION_RATIONALE_REQUIRED: (
        "A non-empty human rationale is required before a disposition can bind."
    ),
    ReasonCode.DISPOSITION_ALREADY_FINAL: (
        "A final test disposition already exists for this exact packet version."
    ),
    ReasonCode.PACKET_NOT_AVAILABLE: "No displayable packet version exists for this case.",
    ReasonCode.ACCESS_DENIED: "This identity is not permitted to perform this action.",
    ReasonCode.SOURCE_QUARANTINED: (
        "A required source is quarantined for content-isolation reasons."
    ),
    ReasonCode.MANIFEST_HASH_MISMATCH: (
        "A source version hash does not match the frozen corpus manifest."
    ),
    ReasonCode.MODEL_CONFIGURATION_MISMATCH: (
        "The active model configuration does not match the authorized pinned configuration."
    ),
    ReasonCode.MODEL_FALLBACK_ATTEMPTED: (
        "A provider or model fallback was attempted and refused."
    ),
    ReasonCode.MODEL_TIMEOUT: "The model call exceeded its frozen per-call timeout.",
    ReasonCode.MODEL_REFUSAL: "The model returned a refusal rather than a schema-valid response.",
    ReasonCode.MODEL_UNAVAILABLE: "The pinned model endpoint is unavailable; no fallback exists.",
    ReasonCode.AUDIT_CHAIN_DIVERGENCE: "The audit chain diverges from its recomputed hashes.",
    ReasonCode.NOT_FOUND: "The requested object does not exist or is not visible to this identity.",
    ReasonCode.INTERNAL_CONTROL_FAILURE: (
        "An internal control could not be completed, so the case failed closed."
    ),
}

#: Reason code produced when each ordered workflow state fails (Section 11.2).
STATE_FAILURE_REASON: dict[CaseState, ReasonCode] = {
    CaseState.AUTHORIZATION_PREFLIGHT: ReasonCode.AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE,
    CaseState.ACTOR_AND_SESSION_VERIFICATION: ReasonCode.REQUESTER_OR_SESSION_INVALID,
    CaseState.REQUEST_NORMALIZATION: ReasonCode.REQUEST_CONTRACT_INVALID,
    CaseState.USE_CASE_AND_RISK_SCOPE: ReasonCode.USE_CASE_EXCLUDED_OR_UNBOUNDED,
    CaseState.EVIDENCE_PLAN: ReasonCode.EVIDENCE_REQUIREMENT_UNRESOLVED,
    CaseState.SOURCE_ELIGIBILITY: ReasonCode.SOURCE_ELIGIBILITY_FAILURE,
    CaseState.READ_ONLY_RETRIEVAL_AND_ISOLATION: ReasonCode.RETRIEVAL_OR_ISOLATION_FAILURE,
    CaseState.EVIDENCE_SUFFICIENCY: ReasonCode.EVIDENCE_INSUFFICIENT_OR_CONFLICTED,
    CaseState.BOUNDED_DRAFT: ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
    CaseState.INDEPENDENT_VERIFICATION: ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
    CaseState.DETERMINISTIC_GOVERNANCE: ReasonCode.DETERMINISTIC_GOVERNANCE_FAILURE,
    CaseState.ROUTE_DETERMINATION: ReasonCode.ROUTE_INVARIANT_FAILURE,
    CaseState.PACKET_ASSEMBLY: ReasonCode.PACKET_ASSEMBLY_FAILURE,
    CaseState.STRUCTURAL_AND_SEMANTIC_VALIDATION: ReasonCode.PACKET_CONTRACT_FAILURE,
    CaseState.PACKET_PRE_ISSUANCE_AUDIT: ReasonCode.CRITICAL_AUDIT_FAILURE,
}


def message_for(code: ReasonCode) -> str:
    return REASON_MESSAGES[code]
