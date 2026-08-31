"""Frozen numeric V1 limits (Sections 10.1 and 15.3).

These are control-plane constants, not tunables. Nothing in the request path, the model
path or the UI may raise them. The frozen configuration file may lower a timeout, but the
hard ceilings below always apply.
"""

from __future__ import annotations

from typing import Final, NamedTuple

from app.domain.reason_codes import ReasonCode


class Limit(NamedTuple):
    key: str
    value: int
    unit: str
    reason_code: ReasonCode


QUESTION_MAX_CHARS: Final[int] = 2_000
SOURCE_PLAN_MAX: Final[int] = 6
RETRIEVAL_CANDIDATE_MAX: Final[int] = 12
EXCERPTS_USED_MAX: Final[int] = 8
EXCERPT_MAX_CHARS: Final[int] = 1_500
TOTAL_EVIDENCE_CONTEXT_MAX_CHARS: Final[int] = 8_000
MODEL_CALLS_MAX: Final[int] = 2
DRAFT_CALLS_MAX: Final[int] = 1
VERIFIER_CALLS_MAX: Final[int] = 1
SAME_ENDPOINT_RETRY_MAX: Final[int] = 1
DRAFT_INPUT_MAX_CHARS: Final[int] = 10_000
VERIFIER_INPUT_MAX_CHARS: Final[int] = 12_000
MODEL_OUTPUT_MAX_CHARS: Final[int] = 6_000
PER_CALL_TIMEOUT_SECONDS: Final[int] = 20
CASE_WALL_CLOCK_SECONDS: Final[int] = 60
CONCURRENT_CASES_MAX: Final[int] = 2
PACKET_EXPORT_MIN_INTERVAL_SECONDS: Final[int] = 30
RATIONALE_MIN_CHARS: Final[int] = 20

#: Machine-readable limit register, surfaced by ``GET /api/v1/admin/configuration`` and
#: asserted by the TEVV at-limit / over-limit scenarios.
LIMIT_REGISTER: Final[tuple[Limit, ...]] = (
    Limit(
        "question_length_chars", QUESTION_MAX_CHARS, "characters", ReasonCode.REQUEST_LIMIT_EXCEEDED
    ),
    Limit("sources_in_plan", SOURCE_PLAN_MAX, "sources", ReasonCode.SOURCE_LIMIT_EXCEEDED),
    Limit(
        "retrieval_candidates",
        RETRIEVAL_CANDIDATE_MAX,
        "candidates",
        ReasonCode.RETRIEVAL_LIMIT_EXCEEDED,
    ),
    Limit("excerpts_used", EXCERPTS_USED_MAX, "excerpts", ReasonCode.EXCERPT_LIMIT_EXCEEDED),
    Limit("excerpt_chars", EXCERPT_MAX_CHARS, "characters", ReasonCode.EXCERPT_SIZE_LIMIT_EXCEEDED),
    Limit(
        "total_evidence_context_chars",
        TOTAL_EVIDENCE_CONTEXT_MAX_CHARS,
        "characters",
        ReasonCode.CONTEXT_LIMIT_EXCEEDED,
    ),
    Limit("model_calls", MODEL_CALLS_MAX, "calls", ReasonCode.MODEL_CALL_LIMIT_EXCEEDED),
    Limit(
        "same_endpoint_retries", SAME_ENDPOINT_RETRY_MAX, "retries", ReasonCode.RETRY_LIMIT_EXCEEDED
    ),
    Limit(
        "model_output_chars",
        MODEL_OUTPUT_MAX_CHARS,
        "characters",
        ReasonCode.MODEL_OUTPUT_LIMIT_EXCEEDED,
    ),
    Limit(
        "case_wall_clock_seconds",
        CASE_WALL_CLOCK_SECONDS,
        "seconds",
        ReasonCode.CASE_WALL_CLOCK_LIMIT_EXCEEDED,
    ),
    Limit("concurrent_cases", CONCURRENT_CASES_MAX, "cases", ReasonCode.CONCURRENCY_LIMIT_EXCEEDED),
    Limit(
        "packet_export_interval_seconds",
        PACKET_EXPORT_MIN_INTERVAL_SECONDS,
        "seconds",
        ReasonCode.EXPORT_RATE_LIMIT_EXCEEDED,
    ),
)

LIMITS_BY_KEY: Final[dict[str, Limit]] = {limit.key: limit for limit in LIMIT_REGISTER}


def limit_register_payload() -> list[dict[str, object]]:
    return [
        {
            "key": limit.key,
            "hard_limit": limit.value,
            "unit": limit.unit,
            "failure_reason_code": limit.reason_code.value,
        }
        for limit in LIMIT_REGISTER
    ]
