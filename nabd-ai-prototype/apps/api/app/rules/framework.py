"""Deterministic rule framework.

Rules are pure functions over a typed context. Each returns a versioned result carrying
its rule ID, version, input references, outcome, reason code, effect, evaluation time and
precedence rank. A model cannot set, waive or reorder a rule (INV-06).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.domain.canonical import utc_now
from app.domain.enums import CaseState, RuleEffect, RuleOutcome
from app.domain.ids import derived_id
from app.domain.reason_codes import ReasonCode
from app.schemas.reasoning import DeterministicResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.services.fixtures import ConflictDeclaration, SourceManifestItem
    from app.schemas.evidence import EvidenceExcerpt
    from app.schemas.governance import (
        AuthorizationDecision,
        IdentityAssertion,
        UseCaseContract,
    )
    from app.schemas.model_io import DraftResponse, VerificationResponse

RULE_SERVICE_ID = "service:deterministic-rule-engine"


@dataclass(slots=True)
class RuleContext:
    """Everything a rule may read. Rules never reach outside this object."""

    case_id: str
    state: CaseState
    evaluated_at: datetime = field(default_factory=utc_now)

    authorization: AuthorizationDecision | None = None
    contract: UseCaseContract | None = None
    contract_extras: dict[str, Any] = field(default_factory=dict)
    identity: IdentityAssertion | None = None
    identity_status: str | None = None

    raw_question: str = ""
    normalised_question: str = ""

    manifest_sha256: str | None = None
    planned_sources: tuple[SourceManifestItem, ...] = ()
    eligible_sources: tuple[SourceManifestItem, ...] = ()
    excluded_sources: tuple[tuple[str, ReasonCode], ...] = ()
    quarantined_sources: tuple[str, ...] = ()
    hash_mismatches: tuple[str, ...] = ()

    excerpts: tuple[EvidenceExcerpt, ...] = ()
    retrieval_candidate_count: int = 0
    total_context_chars: int = 0
    triggered_conflicts: tuple[ConflictDeclaration, ...] = ()

    draft: DraftResponse | None = None
    verification: VerificationResponse | None = None
    material_claim_failures: tuple[str, ...] = ()

    model_calls_used: int = 0
    retries_used: int = 0
    max_model_output_chars: int = 0
    elapsed_seconds: int = 0
    concurrent_cases: int = 0

    packet_payload: dict[str, Any] | None = None
    packet_validation_errors: tuple[str, ...] = ()

    confirmed_pre_issuance_event_id: str | None = None
    confirmed_closure_event_id: str | None = None

    reviewer_identity_id: str | None = None
    reviewer_role_id: str | None = None
    reviewer_scope_id: str | None = None
    reviewer_status: str | None = None
    requester_identity_id: str | None = None
    disposition_rationale: str | None = None

    configured_action_endpoints: tuple[str, ...] = ()
    attempted_action_path: str | None = None

    kill_switch_active: bool = False

    #: Populated by the engine so later rules can read earlier outcomes.
    results: list[DeterministicResult] = field(default_factory=list)

    def result_for(self, rule_id: str) -> DeterministicResult | None:
        for result in self.results:
            if result.rule_id == rule_id:
                return result
        return None


@dataclass(frozen=True, slots=True)
class RuleOutcomeSpec:
    """What a rule decided, before the engine stamps versioning metadata onto it."""

    outcome: RuleOutcome
    reason_code: ReasonCode | str
    effect: RuleEffect
    input_refs: tuple[str, ...] = ()
    detail: str = ""

    @classmethod
    def passed(
        cls, *, input_refs: Sequence[str] = (), detail: str = ""
    ) -> RuleOutcomeSpec:
        return cls(
            outcome=RuleOutcome.PASS,
            reason_code="OK",
            effect=RuleEffect.CONTINUE,
            input_refs=tuple(input_refs),
            detail=detail,
        )

    @classmethod
    def not_applicable(cls, *, detail: str = "") -> RuleOutcomeSpec:
        return cls(
            outcome=RuleOutcome.NOT_APPLICABLE,
            reason_code="NOT_APPLICABLE",
            effect=RuleEffect.CONTINUE,
            detail=detail,
        )

    @classmethod
    def failed(
        cls,
        reason_code: ReasonCode,
        *,
        effect: RuleEffect = RuleEffect.MANDATORY_STOP,
        input_refs: Sequence[str] = (),
        detail: str = "",
    ) -> RuleOutcomeSpec:
        return cls(
            outcome=RuleOutcome.FAIL,
            reason_code=reason_code,
            effect=effect,
            input_refs=tuple(input_refs),
            detail=detail,
        )


RuleFunction = Callable[[RuleContext], RuleOutcomeSpec]


@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    rule_version: str
    precedence_rank: int
    states: frozenset[CaseState]
    purpose: str
    evaluate: RuleFunction

    def applies_to(self, state: CaseState) -> bool:
        return state in self.states


class RuleRegistry:
    """Ordered rule catalog. Precedence is data, not call order."""

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def register(self, rule: Rule) -> Rule:
        if rule.rule_id in self._rules:
            raise ValueError(f"duplicate rule id: {rule.rule_id}")
        self._rules[rule.rule_id] = rule
        return rule

    def all(self) -> tuple[Rule, ...]:
        return tuple(sorted(self._rules.values(), key=lambda r: (r.precedence_rank, r.rule_id)))

    def for_state(self, state: CaseState) -> tuple[Rule, ...]:
        return tuple(rule for rule in self.all() if rule.applies_to(state))

    def get(self, rule_id: str) -> Rule:
        return self._rules[rule_id]

    def ids(self) -> tuple[str, ...]:
        return tuple(rule.rule_id for rule in self.all())


REGISTRY = RuleRegistry()


def rule(
    rule_id: str,
    *,
    version: str,
    precedence: int,
    states: Sequence[CaseState],
    purpose: str,
) -> Callable[[RuleFunction], RuleFunction]:
    def decorator(function: RuleFunction) -> RuleFunction:
        REGISTRY.register(
            Rule(
                rule_id=rule_id,
                rule_version=version,
                precedence_rank=precedence,
                states=frozenset(states),
                purpose=purpose,
                evaluate=function,
            )
        )
        return function

    return decorator


def to_result(rule_def: Rule, context: RuleContext, spec: RuleOutcomeSpec) -> DeterministicResult:
    reason = spec.reason_code.value if isinstance(spec.reason_code, ReasonCode) else spec.reason_code
    return DeterministicResult(
        produced_by=RULE_SERVICE_ID,
        created_at=context.evaluated_at,
        rule_id=rule_def.rule_id,
        rule_version=rule_def.rule_version,
        case_id=context.case_id,
        input_refs=spec.input_refs,
        outcome=spec.outcome,
        reason_code=reason,
        effect=spec.effect,
        precedence_rank=rule_def.precedence_rank,
        evaluated_at=context.evaluated_at,
        detail=spec.detail,
    )


def evaluate_state(context: RuleContext) -> list[DeterministicResult]:
    """Evaluate every rule that applies to ``context.state``, in precedence order.

    Evaluation does not short-circuit: all applicable rules run so that the packet and the
    audit trail record the complete deterministic picture, and the caller then acts on the
    highest-precedence mandatory stop.
    """
    produced: list[DeterministicResult] = []
    for rule_def in REGISTRY.for_state(context.state):
        spec = rule_def.evaluate(context)
        result = to_result(rule_def, context, spec)
        produced.append(result)
        context.results.append(result)
    return produced


def first_mandatory_stop(results: Sequence[DeterministicResult]) -> DeterministicResult | None:
    stops = [result for result in results if result.is_mandatory_stop]
    if not stops:
        return None
    return sorted(stops, key=lambda r: (r.precedence_rank, r.rule_id))[0]


def result_id_for(case_id: str, rule_id: str, occurrence: int = 0) -> str:
    suffix = rule_id.replace("-", "") if occurrence == 0 else f"{rule_id.replace('-', '')}{occurrence}"
    return derived_id("rule_result", case_id, suffix)
