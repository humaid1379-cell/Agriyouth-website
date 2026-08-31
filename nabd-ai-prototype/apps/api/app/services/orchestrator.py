"""The fixed orchestrator.

This module walks the twenty ordered workflow states. It is the only place that advances a
case, and every advance goes through :func:`assert_transition`. A model never selects a
state, a tool or a route; it is called exactly twice, from stages 8 and 9, and its output
is data that later stages validate.

The ``ProcessOptions`` fault hooks exist for the TEVV harness. They are service-layer
arguments: no API route, request body or browser input can set them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.mock_adapter import DeterministicMockAdapter
from app.adapters.protocol import ModelAdapter, ModelAdapterError, ModelFault
from app.config import get_settings
from app.domain.canonical import text_sha256, utc_now
from app.domain.enums import (
    AuditEventType,
    AuditOutcome,
    CaseState,
    DataClassification,
    Materiality,
    ModelMode,
    ModelTaskRole,
    Route,
    RuleEffect,
    RuleOutcome,
    Severity,
    SupportState,
    UncertaintyKind,
)
from app.domain.errors import ControlError, IllegalTransitionError, StopError
from app.domain.fsm import assert_transition, next_state
from app.domain.ids import derived_id, new_id
from app.domain.limits import CONCURRENT_CASES_MAX, SOURCE_PLAN_MAX
from app.domain.reason_codes import ReasonCode, message_for
from app.domain.versions import COMPONENT_VERSIONS
from app.repositories.tables import (
    CaseRow,
    CaseStateTransitionRow,
    ClaimEvidenceLinkRow,
    DecisionPacketRow,
    DeterministicResultRow,
    EvidenceExcerptRow,
    GeneratedClaimRow,
    ModelRunRow,
    UncertaintyRecordRow,
)
from app.rules import RuleContext, assert_catalog_loaded, evaluate_state, first_mandatory_stop
from app.schemas.audit import ObjectBinding
from app.schemas.evidence import EvidenceExcerpt
from app.schemas.governance import IdentityAssertion
from app.schemas.model_io import DraftRequest, VerificationRequest
from app.schemas.packet import DecisionReadinessPacket, StopRecord
from app.schemas.reasoning import (
    ClaimEvidenceLink,
    DeterministicResult,
    GeneratedClaim,
    UncertaintyRecord,
)
from app.services import audit
from app.services.eligibility import evaluate_source_eligibility
from app.services.fixtures import (
    SourceManifestItem,
    active_model_configuration,
    contract_extras,
    load_corpus_fixtures,
    load_use_case_contract,
    primary_authorization,
)
from app.services.kill_switch import kill_switch_active
from app.services.model_gateway import ModelGateway
from app.services.packet import (
    PacketInputs,
    SemanticContext,
    build_packet,
    build_risk_profile,
    validate_packet_semantics,
)
from app.services.prompts import build_draft_input, build_verification_input
from app.services.retrieval import retrieve

ORCHESTRATOR_SERVICE_ID = "service:fixed-orchestrator"


@dataclass(slots=True)
class ProcessOptions:
    """Service-layer test hooks for the frozen TEVV scenarios. Never API-reachable."""

    fault: ModelFault = ModelFault.NONE
    omit_rule_id: str | None = None
    skip_pre_issuance_audit: bool = False
    attempted_action_path: str | None = None
    configured_action_endpoints: tuple[str, ...] = ()
    attempt_third_model_call: bool = False
    simulate_hash_mismatch: bool = False
    simulate_elapsed_seconds: int | None = None
    concurrent_cases_override: int | None = None
    authorization_id_override: str | None = None
    adapter_override: ModelAdapter | None = None


@dataclass(slots=True)
class ProcessResult:
    case_id: str
    terminal_state: CaseState
    route: Route
    reason_code: str | None
    packet: DecisionReadinessPacket | None = None
    stop_record: StopRecord | None = None
    rule_results: tuple[DeterministicResult, ...] = ()
    excerpts: tuple[EvidenceExcerpt, ...] = ()
    claims: tuple[GeneratedClaim, ...] = ()
    model_calls: int = 0
    pre_issuance_event_id: str | None = None

    @property
    def stopped(self) -> bool:
        return self.route is Route.CANNOT_PROCEED


class CaseProcessor:
    """Runs one case through the ordered workflow. One instance per processing attempt."""

    def __init__(
        self,
        session: Session,
        case: CaseRow,
        identity: IdentityAssertion,
        options: ProcessOptions | None = None,
    ) -> None:
        self.session = session
        self.case = case
        self.identity = identity
        self.options = options or ProcessOptions()
        self.settings = get_settings()
        self.started_at = utc_now()

        self.corpus = load_corpus_fixtures()
        self.contract = load_use_case_contract()
        self.extras = contract_extras()
        self.authorization = primary_authorization()
        if self.options.authorization_id_override:
            from app.services.fixtures import load_authorizations

            self.authorization = load_authorizations()[self.options.authorization_id_override]

        self.state = CaseState(case.current_state)
        self.transition_sequence = self._current_transition_sequence()
        self.results: list[DeterministicResult] = []
        self.excerpts: tuple[EvidenceExcerpt, ...] = ()
        self.eligible: tuple[SourceManifestItem, ...] = ()
        self.planned: tuple[SourceManifestItem, ...] = ()
        self.quarantined: tuple[str, ...] = ()
        self.hash_mismatches: tuple[str, ...] = ()
        self.triggered_conflicts: tuple[Any, ...] = ()
        self.uncertainty: list[UncertaintyRecord] = []
        self.claims: tuple[GeneratedClaim, ...] = ()
        self.gateway: ModelGateway | None = None
        self.packet: DecisionReadinessPacket | None = None
        self.retrieval_candidates = 0
        self.total_context_chars = 0
        self.pre_issuance_event_id: str | None = None
        self._result_counter = 0

    # -- infrastructure ----------------------------------------------------------
    def _current_transition_sequence(self) -> int:
        rows = (
            self.session.execute(
                select(CaseStateTransitionRow.sequence)
                .where(CaseStateTransitionRow.case_id == self.case.case_id)
                .order_by(CaseStateTransitionRow.sequence.desc())
            )
            .scalars()
            .first()
        )
        return int(rows or 0)

    def _elapsed_seconds(self) -> int:
        if self.options.simulate_elapsed_seconds is not None:
            return self.options.simulate_elapsed_seconds
        return int((utc_now() - self.started_at).total_seconds())

    def _concurrent_cases(self) -> int:
        if self.options.concurrent_cases_override is not None:
            return self.options.concurrent_cases_override
        return int(
            self.session.execute(
                select(CaseRow).where(
                    CaseRow.processing_started_at.is_not(None),
                    CaseRow.processing_completed_at.is_(None),
                    CaseRow.case_id != self.case.case_id,
                )
            )
            .scalars()
            .all()
            .__len__()
        )

    def _transition_to(self, target: CaseState, reason_code: ReasonCode | None = None) -> None:
        assert_transition(self.case.case_id, self.state, target)
        self.transition_sequence += 1
        self.session.add(
            CaseStateTransitionRow(
                transition_id=derived_id(
                    "event", self.case.case_id, f"t{self.transition_sequence}"
                ),
                case_id=self.case.case_id,
                sequence=self.transition_sequence,
                from_state=self.state.value,
                to_state=target.value,
                reason_code=reason_code.value if reason_code else None,
                actor_id=ORCHESTRATOR_SERVICE_ID,
                actor_kind="SERVICE",
                component_versions=dict(COMPONENT_VERSIONS),
                applicable_rule_versions=sorted(
                    {f"{r.rule_id}@{r.rule_version}" for r in self.results}
                ),
                occurred_at=utc_now(),
            )
        )
        audit.record(
            self.session,
            event_type=AuditEventType.STATE_TRANSITION,
            actor_id=ORCHESTRATOR_SERVICE_ID,
            outcome=AuditOutcome.PASS if reason_code is None else AuditOutcome.FAIL,
            case_id=self.case.case_id,
            from_state=self.state,
            to_state=target,
            reason_code=reason_code.value if reason_code else None,
        )
        self.state = target
        self.case.current_state = target.value
        self.case.updated_at = utc_now()
        self.session.flush()

    def _context(self) -> RuleContext:
        return RuleContext(
            case_id=self.case.case_id,
            state=self.state,
            evaluated_at=utc_now(),
            authorization=self.authorization,
            contract=self.contract,
            contract_extras=self.extras,
            identity=self.identity,
            identity_status=self.identity.status.value,
            raw_question=self.case.raw_question,
            normalised_question=self.case.normalised_question,
            manifest_sha256=self.corpus.manifest_sha256,
            planned_sources=self.planned,
            eligible_sources=self.eligible,
            quarantined_sources=self.quarantined,
            hash_mismatches=self.hash_mismatches,
            excerpts=self.excerpts,
            retrieval_candidate_count=self.retrieval_candidates,
            total_context_chars=self.total_context_chars,
            triggered_conflicts=tuple(self.triggered_conflicts),
            model_calls_used=self.gateway.budget.total_calls if self.gateway else 0,
            retries_used=self.gateway.budget.retries if self.gateway else 0,
            max_model_output_chars=max(
                (run.output_chars for run in (self.gateway.runs if self.gateway else [])),
                default=0,
            ),
            elapsed_seconds=self._elapsed_seconds(),
            concurrent_cases=self._concurrent_cases(),
            configured_action_endpoints=self.options.configured_action_endpoints,
            attempted_action_path=self.options.attempted_action_path,
            kill_switch_active=kill_switch_active(self.session),
            requester_identity_id=self.case.requester_identity_id,
        )

    def _persist_results(self, results: list[DeterministicResult]) -> None:
        for result in results:
            self._result_counter += 1
            self.session.add(
                DeterministicResultRow(
                    deterministic_result_id=derived_id(
                        "rule_result", self.case.case_id, f"{self._result_counter:03d}"
                    ),
                    case_id=self.case.case_id,
                    rule_id=result.rule_id,
                    rule_version=result.rule_version,
                    outcome=result.outcome.value,
                    reason_code=result.reason_code,
                    effect=result.effect.value,
                    precedence_rank=result.precedence_rank,
                    evaluated_at=result.evaluated_at,
                    payload=result.model_dump(mode="json"),
                )
            )
            if result.outcome is RuleOutcome.FAIL:
                audit.record(
                    self.session,
                    event_type=AuditEventType.DETERMINISTIC_RULE_RESULT,
                    actor_id=ORCHESTRATOR_SERVICE_ID,
                    outcome=AuditOutcome.FAIL,
                    case_id=self.case.case_id,
                    reason_code=result.reason_code,
                    severity=(
                        Severity.S0_CRITICAL
                        if result.reason_code == ReasonCode.PROHIBITED_ACTION_PATH_DETECTED.value
                        else None
                    ),
                    binding=ObjectBinding(
                        object_kind="deterministic_result",
                        object_id=result.rule_id,
                        object_version=result.rule_version,
                    ),
                )
        self.results.extend(results)
        self.session.flush()

    def _evaluate(self, context: RuleContext | None = None) -> DeterministicResult | None:
        """Run applicable rules for the current state and return the governing stop, if any."""
        ctx = context or self._context()
        assert_catalog_loaded()
        evaluated = evaluate_state(ctx)
        if not evaluated:
            # A state with no applicable rule would pass unconditionally. That is a
            # governance failure, not a fast path.
            raise StopError(
                ReasonCode.DETERMINISTIC_GOVERNANCE_FAILURE,
                case_id=self.case.case_id,
                state=self.state,
            )
        produced = [result for result in evaluated if result.rule_id != self.options.omit_rule_id]
        if self.options.omit_rule_id and any(
            result.rule_id == self.options.omit_rule_id for result in ctx.results
        ):
            # A rule that should have been evaluated is missing from this run: that is a
            # governance failure in its own right, never a silent pass.
            produced.append(
                DeterministicResult(
                    produced_by=ORCHESTRATOR_SERVICE_ID,
                    rule_id="GOV-MISSING",
                    rule_version="1.0.0",
                    case_id=self.case.case_id,
                    input_refs=(self.options.omit_rule_id,),
                    outcome=RuleOutcome.FAIL,
                    reason_code=ReasonCode.DETERMINISTIC_GOVERNANCE_FAILURE.value,
                    effect=RuleEffect.MANDATORY_STOP,
                    precedence_rank=0,
                    evaluated_at=ctx.evaluated_at,
                    detail="A rule in the frozen catalog did not evaluate for this state.",
                )
            )
        self._persist_results(produced)
        return first_mandatory_stop(produced)

    def _stop(self, reason: ReasonCode, detail: str = "") -> ProcessResult:
        failed_state = self.state
        record = StopRecord(
            produced_by=ORCHESTRATOR_SERVICE_ID,
            stop_record_id=derived_id("stop", self.case.case_id, "001"),
            case_id=self.case.case_id,
            failed_state=failed_state.value,
            reason_code=reason.value,
            message=detail or message_for(reason),
            rule_results=tuple(self.results),
            uncertainty=tuple(self.uncertainty),
            occurred_at=utc_now(),
        )
        self._transition_to(CaseState.CANNOT_PROCEED, reason)
        self.case.route = Route.CANNOT_PROCEED.value
        self.case.reason_code = reason.value
        self.case.stop_record = record.model_dump(mode="json")
        self.case.processing_completed_at = utc_now()
        self.session.flush()
        return ProcessResult(
            case_id=self.case.case_id,
            terminal_state=CaseState.CANNOT_PROCEED,
            route=Route.CANNOT_PROCEED,
            reason_code=reason.value,
            stop_record=record,
            rule_results=tuple(self.results),
            excerpts=self.excerpts,
            claims=self.claims,
            model_calls=self.gateway.budget.total_calls if self.gateway else 0,
        )

    # -- the ordered workflow -----------------------------------------------------
    def run(self) -> ProcessResult:
        self.case.processing_started_at = self.started_at
        self.session.flush()
        try:
            return self._run_stages()
        except IllegalTransitionError as error:
            audit.record(
                self.session,
                event_type=AuditEventType.SECURITY_EVENT,
                actor_id=ORCHESTRATOR_SERVICE_ID,
                outcome=AuditOutcome.DENIED,
                case_id=self.case.case_id,
                reason_code=ReasonCode.ILLEGAL_STATE_TRANSITION.value,
                severity=Severity.S0_CRITICAL,
            )
            raise error
        except ControlError as error:
            return self._stop(error.code, error.message)

    def _run_stages(self) -> ProcessResult:
        # Stage 0 - AUTHORIZATION_PREFLIGHT
        if self.options.simulate_hash_mismatch:
            self.hash_mismatches = ("POL-001@v1",)
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))
        audit.record(
            self.session,
            event_type=AuditEventType.AUTHORIZATION_CHECK,
            actor_id=ORCHESTRATOR_SERVICE_ID,
            outcome=AuditOutcome.PASS,
            case_id=self.case.case_id,
            binding=ObjectBinding(
                object_kind="authorization_decision",
                object_id=self.authorization.authorization_id,
            ),
        )

        # Stage 1 - ACTOR_AND_SESSION_VERIFICATION
        self._transition_to(next_state(self.state))
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))
        audit.record(
            self.session,
            event_type=AuditEventType.IDENTITY_VERIFICATION,
            actor_id=self.identity.identity_id,
            actor_kind="HUMAN_DEMO_IDENTITY",
            outcome=AuditOutcome.PASS,
            case_id=self.case.case_id,
        )

        # Stage 2 - REQUEST_NORMALIZATION
        self._transition_to(next_state(self.state))
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 3 - USE_CASE_AND_RISK_SCOPE
        self._transition_to(next_state(self.state))
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 4 - EVIDENCE_PLAN
        self._transition_to(next_state(self.state))
        report = evaluate_source_eligibility(
            at=utc_now(),
            business_scope_id=self.authorization.business_scope_id,
            use_case_contract_id=self.contract.use_case_contract_id,
            access_labels=frozenset({"INTERNAL_SYNTHETIC"}),
            verify_file_hashes=not self.options.simulate_hash_mismatch,
            fixtures=self.corpus,
        )
        self.planned = report.eligible[:SOURCE_PLAN_MAX]
        if not self.planned and not self.options.simulate_hash_mismatch:
            return self._stop(ReasonCode.EVIDENCE_REQUIREMENT_UNRESOLVED)
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 5 - SOURCE_ELIGIBILITY
        self._transition_to(next_state(self.state))
        self.eligible = report.eligible
        self.quarantined = report.quarantined
        if self.options.simulate_hash_mismatch:
            self.hash_mismatches = ("POL-001@v1",)
        stop = self._evaluate()
        audit.record(
            self.session,
            event_type=AuditEventType.SOURCE_ELIGIBILITY,
            actor_id=ORCHESTRATOR_SERVICE_ID,
            outcome=AuditOutcome.PASS if not stop else AuditOutcome.FAIL,
            case_id=self.case.case_id,
            reason_code=stop.reason_code if stop else None,
            payload_reference=f"eligible={len(self.eligible)};excluded={len(report.excluded_keys)}",
        )
        if stop:
            return self._stop(ReasonCode(stop.reason_code))
        for excluded_key in report.excluded_keys:
            decision = next(d for d in report.decisions if d.source_key == excluded_key)
            if decision.reason_code == ReasonCode.SOURCE_QUARANTINED.value:
                audit.record(
                    self.session,
                    event_type=AuditEventType.SECURITY_EVENT,
                    actor_id=ORCHESTRATOR_SERVICE_ID,
                    outcome=AuditOutcome.DENIED,
                    case_id=self.case.case_id,
                    reason_code=ReasonCode.SOURCE_QUARANTINED.value,
                    severity=Severity.S2_MODERATE,
                    binding=ObjectBinding(object_kind="source_version", object_id=excluded_key),
                )

        # Stage 6 - READ_ONLY_RETRIEVAL_AND_ISOLATION
        self._transition_to(next_state(self.state))
        retrieval = retrieve(
            self.session,
            case_id=self.case.case_id,
            question=self.case.normalised_question,
            eligible=self.eligible,
        )
        self.excerpts = retrieval.excerpts
        self.retrieval_candidates = retrieval.candidate_count
        self.total_context_chars = retrieval.total_context_chars
        self._persist_excerpts()
        audit.record(
            self.session,
            event_type=AuditEventType.RETRIEVAL,
            actor_id=ORCHESTRATOR_SERVICE_ID,
            outcome=AuditOutcome.PASS,
            case_id=self.case.case_id,
            payload_reference=(
                f"candidates={retrieval.candidate_count};admitted={len(retrieval.excerpts)};"
                f"chars={retrieval.total_context_chars}"
            ),
        )
        if not self.excerpts:
            return self._stop(ReasonCode.RETRIEVAL_OR_ISOLATION_FAILURE)
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 7 - EVIDENCE_SUFFICIENCY
        self._transition_to(next_state(self.state))
        self.triggered_conflicts = self._detect_conflicts()
        self._record_uncertainty()
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 8 - BOUNDED_DRAFT
        self._transition_to(next_state(self.state))
        self.gateway = self._build_gateway()
        try:
            draft_request = DraftRequest(
                case_id=self.case.case_id,
                normalised_question=self.case.normalised_question,
                permitted_purpose=self.contract.permitted_purpose,
                output_schema_id="draft-response-v1",
                prompt_version=self.gateway.draft_configuration.prompt_version,
                excerpts=self.excerpts,
                rendered_input=build_draft_input(
                    normalised_question=self.case.normalised_question,
                    permitted_purpose=self.contract.permitted_purpose,
                    excerpts=self.excerpts,
                ),
            )
            draft_outcome = self.gateway.draft(draft_request)
        except ModelAdapterError as error:
            self._persist_model_runs()
            self._record_model_audit(succeeded=False, reason_code=error.code.value)
            return self._stop(self._model_stop_reason(error.code))
        self._persist_model_runs()
        self._record_model_audit(succeeded=True, reason_code=None)
        draft = draft_outcome.draft
        assert draft is not None
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 9 - INDEPENDENT_VERIFICATION
        self._transition_to(next_state(self.state))
        try:
            verification_request = VerificationRequest(
                case_id=self.case.case_id,
                output_schema_id="verification-response-v1",
                prompt_version=self.gateway.verify_configuration.prompt_version,
                draft_claims=draft.claims,
                excerpts=self.excerpts,
                rendered_input=build_verification_input(
                    draft_claims=draft.claims, excerpts=self.excerpts
                ),
            )
            verify_outcome = self.gateway.verify(verification_request)
            if self.options.attempt_third_model_call:
                # A third call must be refused by the budget, not by convention.
                self.gateway.verify(verification_request)
        except ModelAdapterError as error:
            self._persist_model_runs()
            self._record_model_audit(succeeded=False, reason_code=error.code.value)
            return self._stop(self._model_stop_reason(error.code))
        self._persist_model_runs()
        self._record_model_audit(succeeded=True, reason_code=None)
        verification = verify_outcome.verification
        assert verification is not None

        self.claims = self._bind_claims(draft, verification)
        self._persist_claims()
        context = self._context()
        context.draft = draft
        context.verification = verification
        context.material_claim_failures = tuple(
            claim.claim_ref for claim in self.claims if claim.is_blocking
        )
        stop = self._evaluate(context)
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 10 - DETERMINISTIC_GOVERNANCE
        self._transition_to(next_state(self.state))
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))
        if any(result.is_mandatory_stop for result in self.results):
            return self._stop(ReasonCode.DETERMINISTIC_GOVERNANCE_FAILURE)

        # Stage 11 - ROUTE_DETERMINATION
        self._transition_to(next_state(self.state))
        route = Route.HUMAN_REVIEW_REQUIRED
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 12 - PACKET_ASSEMBLY
        #
        # The pre-issuance event id is generated before the packet is sealed so that the
        # packet can carry its own audit reference inside the sealed preimage. The event is
        # written at stage 14 under exactly this id, binding the resulting hash, which is
        # why the two never disagree.
        self._transition_to(next_state(self.state))
        self.pre_issuance_event_id = new_id("event")
        packet = self._assemble_packet(route)
        self.packet = packet
        audit.record(
            self.session,
            event_type=AuditEventType.PACKET_CREATED,
            actor_id=ORCHESTRATOR_SERVICE_ID,
            outcome=AuditOutcome.PASS,
            case_id=self.case.case_id,
            binding=ObjectBinding(
                object_kind="decision_packet",
                object_id=packet.identity.packet_id,
                object_version=str(packet.identity.packet_version),
                object_sha256=packet.integrity.packet_sha256,
            ),
        )
        stop = self._evaluate()
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 13 - STRUCTURAL_AND_SEMANTIC_VALIDATION
        self._transition_to(next_state(self.state))
        semantic_context = SemanticContext(
            case_id=self.case.case_id,
            authorization=self.authorization,
            eligible_source_keys=frozenset(item.source_key for item in self.eligible),
            admitted_excerpt_ids=frozenset(e.excerpt_id for e in self.excerpts),
            issued_packet_sha256=packet.integrity.packet_sha256,
            confirmed_pre_issuance_event_id=self.pre_issuance_event_id,
        )
        failures = validate_packet_semantics(packet, semantic_context)
        context = self._context()
        context.packet_payload = packet.model_dump(mode="json")
        context.packet_validation_errors = failures
        stop = self._evaluate(context)
        audit.record(
            self.session,
            event_type=AuditEventType.PACKET_VALIDATED,
            actor_id=ORCHESTRATOR_SERVICE_ID,
            outcome=AuditOutcome.PASS if not failures else AuditOutcome.FAIL,
            case_id=self.case.case_id,
            reason_code=ReasonCode.PACKET_CONTRACT_FAILURE.value if failures else None,
            payload_reference=";".join(failures[:4]),
        )
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        # Stage 14 - PACKET_PRE_ISSUANCE_AUDIT
        self._transition_to(next_state(self.state))
        confirmed_event_id: str | None = None
        if not self.options.skip_pre_issuance_audit:
            confirmed = audit.record_and_confirm(
                self.session,
                event_type=AuditEventType.PACKET_PRE_ISSUANCE,
                actor_id=ORCHESTRATOR_SERVICE_ID,
                outcome=AuditOutcome.PASS,
                case_id=self.case.case_id,
                event_id=self.pre_issuance_event_id,
                binding=ObjectBinding(
                    object_kind="decision_packet",
                    object_id=packet.identity.packet_id,
                    object_version=str(packet.identity.packet_version),
                    object_sha256=packet.integrity.packet_sha256,
                ),
            )
            confirmed_event_id = confirmed.event_id
        else:
            self.pre_issuance_event_id = None
        context = self._context()
        context.confirmed_pre_issuance_event_id = confirmed_event_id
        stop = self._evaluate(context)
        if stop:
            return self._stop(ReasonCode(stop.reason_code))

        self.packet = packet
        self._persist_packet(packet, displayable=True)

        # Stage 15 - AWAITING_AUTHORIZED_HUMAN_REVIEW
        self._transition_to(next_state(self.state))
        self.case.route = route.value
        self.case.reason_code = None
        self.case.processing_completed_at = utc_now()
        self.session.flush()

        return ProcessResult(
            case_id=self.case.case_id,
            terminal_state=CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW,
            route=route,
            reason_code=None,
            packet=packet,
            rule_results=tuple(self.results),
            excerpts=self.excerpts,
            claims=self.claims,
            model_calls=self.gateway.budget.total_calls if self.gateway else 0,
            pre_issuance_event_id=self.pre_issuance_event_id,
        )

    # -- helpers ------------------------------------------------------------------
    def _build_gateway(self) -> ModelGateway:
        draft_configuration = active_model_configuration(ModelTaskRole.DRAFTER)
        verify_configuration = active_model_configuration(ModelTaskRole.VERIFIER)
        adapter: ModelAdapter
        if self.options.adapter_override is not None:
            adapter = self.options.adapter_override
        elif self.settings.model_mode is ModelMode.LIVE:
            from app.adapters.openai_compatible import OpenAICompatibleAdapter

            adapter = OpenAICompatibleAdapter(
                self.settings, draft_configuration, verify_configuration
            )
        else:
            adapter = DeterministicMockAdapter(fault=self.options.fault)
        return ModelGateway(
            adapter=adapter,
            draft_configuration=draft_configuration,
            verify_configuration=verify_configuration,
            mode=self.settings.model_mode,
        )

    @staticmethod
    def _model_stop_reason(code: ReasonCode) -> ReasonCode:
        if code in {
            ReasonCode.MODEL_CALL_LIMIT_EXCEEDED,
            ReasonCode.RETRY_LIMIT_EXCEEDED,
            ReasonCode.MODEL_OUTPUT_LIMIT_EXCEEDED,
        }:
            return code
        return ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE

    def _persist_excerpts(self) -> None:
        for excerpt in self.excerpts:
            self.session.add(
                EvidenceExcerptRow(
                    excerpt_id=excerpt.excerpt_id,
                    case_id=excerpt.case_id,
                    source_id=excerpt.source_id,
                    source_version=excerpt.source_version,
                    source_version_key=f"{excerpt.source_id}@{excerpt.source_version}",
                    page_number=excerpt.page_number,
                    section_heading=excerpt.section_heading,
                    block_index=excerpt.block_index,
                    char_start=excerpt.char_start,
                    char_end=excerpt.char_end,
                    text=excerpt.text,
                    text_sha256=excerpt.text_sha256,
                    source_sha256=excerpt.source_sha256,
                    rank=excerpt.rank,
                    retrieval_score=excerpt.retrieval_score,
                    admitted=True,
                    payload=excerpt.model_dump(mode="json"),
                    created_at=excerpt.created_at,
                )
            )
        self.session.flush()

    def _persist_model_runs(self) -> None:
        if self.gateway is None:
            return
        existing = set(
            self.session.execute(
                select(ModelRunRow.model_run_id).where(ModelRunRow.case_id == self.case.case_id)
            ).scalars()
        )
        for run in self.gateway.runs:
            if run.model_run_id in existing:
                continue
            self.session.add(
                ModelRunRow(
                    model_run_id=run.model_run_id,
                    case_id=run.case_id,
                    model_configuration_id=run.model_configuration_id,
                    task_role=run.task_role.value,
                    call_index=run.call_index,
                    retry_count=run.retry_count,
                    input_chars=run.input_chars,
                    output_chars=run.output_chars,
                    input_sha256=run.input_sha256,
                    output_sha256=run.output_sha256,
                    duration_ms=run.duration_ms,
                    succeeded=run.succeeded,
                    reason_code=run.reason_code,
                    mode=run.mode.value,
                    payload=run.model_dump(mode="json"),
                    created_at=run.created_at,
                )
            )
        self.session.flush()

    def _record_model_audit(self, *, succeeded: bool, reason_code: str | None) -> None:
        if self.gateway is None:
            return
        latest = self.gateway.runs[-1] if self.gateway.runs else None
        audit.record(
            self.session,
            event_type=AuditEventType.MODEL_EXECUTION,
            actor_id=f"service:model-adapter:{self.gateway.adapter.name}",
            outcome=AuditOutcome.PASS if succeeded else AuditOutcome.FAIL,
            case_id=self.case.case_id,
            reason_code=reason_code,
            binding=(
                ObjectBinding(
                    object_kind="model_run",
                    object_id=latest.model_run_id,
                    object_version=latest.model_configuration_id,
                    object_sha256=latest.output_sha256,
                )
                if latest
                else None
            ),
            payload_reference=(
                f"calls={self.gateway.budget.total_calls};retries={self.gateway.budget.retries}"
            ),
        )

    def _detect_conflicts(self) -> tuple[Any, ...]:
        admitted_keys = {f"{e.source_id}@{e.source_version}" for e in self.excerpts}
        triggered = []
        for conflict in self.corpus.conflicts:
            if not conflict.question_triggers(self.case.normalised_question):
                continue
            if conflict.party_a_source_key in admitted_keys and (
                conflict.party_b_source_key in admitted_keys
            ):
                triggered.append(conflict)
        return tuple(triggered)

    def _record_uncertainty(self) -> None:
        now = utc_now()
        for conflict in self.triggered_conflicts:
            self.uncertainty.append(
                UncertaintyRecord(
                    produced_by=ORCHESTRATOR_SERVICE_ID,
                    created_at=now,
                    uncertainty_id=derived_id(
                        "uncertainty", self.case.case_id, conflict.conflict_id
                    ),
                    case_id=self.case.case_id,
                    kind=UncertaintyKind.SOURCE_CONFLICT,
                    description_en=conflict.description_en,
                    description_ar=conflict.description_ar,
                    affected_source_ids=(
                        conflict.party_a_source_key,
                        conflict.party_b_source_key,
                    ),
                    increases_risk=True,
                )
            )
        if self.quarantined:
            self.uncertainty.append(
                UncertaintyRecord(
                    produced_by=ORCHESTRATOR_SERVICE_ID,
                    created_at=now,
                    uncertainty_id=derived_id("uncertainty", self.case.case_id, "QUARANTINE"),
                    case_id=self.case.case_id,
                    kind=UncertaintyKind.SCOPE_LIMIT,
                    description_en=(
                        "One or more sources were quarantined for instruction-like content and "
                        "excluded before retrieval. They cannot support any claim."
                    ),
                    description_ar=(
                        "تم عزل مصدر أو أكثر لاحتوائه على نص شبيه بالتعليمات، واستُبعد قبل "
                        "الاسترجاع. ولا يمكنه دعم أي ادعاء."
                    ),
                    affected_source_ids=self.quarantined,
                    increases_risk=True,
                )
            )
        for record in self.uncertainty:
            self.session.add(
                UncertaintyRecordRow(
                    uncertainty_id=record.uncertainty_id,
                    case_id=record.case_id,
                    kind=record.kind.value,
                    payload=record.model_dump(mode="json"),
                    created_at=record.created_at,
                )
            )
        self.session.flush()

    def _bind_claims(self, draft: Any, verification: Any) -> tuple[GeneratedClaim, ...]:
        """Bind verified claims to exact evidence, re-checking every quote independently.

        The verifier's own assertion that a quote exists is not trusted: the offsets are
        re-sliced from the stored excerpt here, and a quote that does not reproduce marks
        the link unverified, which in turn blocks a material claim.
        """
        by_excerpt = {excerpt.excerpt_id: excerpt for excerpt in self.excerpts}
        draft_by_ref = {claim.claim_ref: claim for claim in draft.claims}
        draft_run = next(
            (
                r
                for r in (self.gateway.runs if self.gateway else [])
                if r.task_role is ModelTaskRole.DRAFTER
            ),
            None,
        )
        verify_run = next(
            (
                r
                for r in (self.gateway.runs if self.gateway else [])
                if r.task_role is ModelTaskRole.VERIFIER
            ),
            None,
        )
        bound: list[GeneratedClaim] = []
        now = utc_now()

        for verified in verification.verified_claims:
            source_claim = draft_by_ref.get(verified.claim_ref)
            if source_claim is None:
                continue
            links: list[ClaimEvidenceLink] = []
            for span in verified.support_spans:
                excerpt = by_excerpt.get(span.excerpt_id)
                if excerpt is None:
                    continue
                actual = excerpt.text[span.quote_start : span.quote_end]
                links.append(
                    ClaimEvidenceLink(
                        excerpt_id=excerpt.excerpt_id,
                        source_id=excerpt.source_id,
                        source_version=excerpt.source_version,
                        page_number=excerpt.page_number,
                        section_heading=excerpt.section_heading,
                        char_start=excerpt.char_start + span.quote_start,
                        char_end=excerpt.char_start + span.quote_end,
                        quoted_text=actual,
                        quote_verified=actual == span.quoted_text,
                    )
                )
            support_state = verified.support_state
            if support_state is SupportState.SUPPORTED and (
                not links or not all(link.quote_verified for link in links)
            ):
                support_state = SupportState.UNSUPPORTED
            bound.append(
                GeneratedClaim(
                    produced_by=ORCHESTRATOR_SERVICE_ID,
                    created_at=now,
                    claim_id=derived_id("claim", self.case.case_id, verified.claim_ref),
                    case_id=self.case.case_id,
                    claim_ref=verified.claim_ref,
                    statement=source_claim.statement,
                    materiality=source_claim.materiality,
                    support_state=support_state,
                    evidence_links=tuple(links),
                    support_spans=verified.support_spans,
                    conflict_ids=verified.conflict_ids,
                    qualification=verified.qualification,
                    verification_note=verified.verification_note,
                    draft_model_run_id=draft_run.model_run_id if draft_run else "unknown",
                    verifier_model_run_id=verify_run.model_run_id if verify_run else "unknown",
                )
            )
        return tuple(bound)

    def _persist_claims(self) -> None:
        for claim in self.claims:
            self.session.add(
                GeneratedClaimRow(
                    claim_id=claim.claim_id,
                    case_id=claim.case_id,
                    claim_ref=claim.claim_ref,
                    statement=claim.statement,
                    materiality=claim.materiality.value,
                    support_state=claim.support_state.value,
                    payload=claim.model_dump(mode="json"),
                    created_at=claim.created_at,
                )
            )
        # Claims must exist before their evidence links: the unit of work batches inserts
        # per mapper, so an interleaved add would emit the links first.
        self.session.flush()
        for claim in self.claims:
            for link in claim.evidence_links:
                self.session.add(
                    ClaimEvidenceLinkRow(
                        claim_evidence_link_id=f"{claim.claim_id}:{link.excerpt_id}",
                        claim_id=claim.claim_id,
                        excerpt_id=link.excerpt_id,
                        case_id=claim.case_id,
                        quote_start=link.char_start,
                        quote_end=link.char_end,
                        quoted_text=link.quoted_text,
                        quote_verified=link.quote_verified,
                    )
                )
        self.session.flush()

    def _assemble_packet(self, route: Route) -> DecisionReadinessPacket:
        material_count = sum(
            1 for claim in self.claims if claim.materiality is Materiality.MATERIAL
        )
        risk = build_risk_profile(
            material_claim_count=material_count,
            uncertainty=tuple(self.uncertainty),
            conflicts=tuple(c.conflict_id for c in self.triggered_conflicts),
            quarantined_sources=self.quarantined,
        )
        inputs = PacketInputs(
            case_id=self.case.case_id,
            packet_id=derived_id("packet", self.case.case_id, "v1"),
            packet_version=1,
            authorization=self.authorization,
            requester_identity_id=self.case.requester_identity_id,
            requester_role=self.identity.role,
            submitted_at=self.case.submitted_at,
            normalised_question=self.case.normalised_question,
            question_sha256=self.case.question_sha256,
            permitted_purpose=self.contract.permitted_purpose,
            excerpts=self.excerpts,
            source_items=self.eligible,
            claims=self.claims,
            rule_results=tuple(self.results),
            uncertainty=tuple(self.uncertainty),
            conflicts=tuple(c.conflict_id for c in self.triggered_conflicts),
            risk=risk,
            route=route,
            route_reason_code="HUMAN_REVIEW_REQUIRED_BY_DESIGN",
            pre_issuance_event_id=self.pre_issuance_event_id,
            audit_chain_head_hash=audit.verify_chain(self.session, self.case.case_id).head_hash,
            draft_configuration_id=(
                self.gateway.draft_configuration.model_configuration_id if self.gateway else ""
            ),
            verifier_configuration_id=(
                self.gateway.verify_configuration.model_configuration_id if self.gateway else ""
            ),
            created_at=utc_now(),
        )
        return build_packet(inputs)

    def _persist_packet(self, packet: DecisionReadinessPacket, *, displayable: bool) -> None:
        from app.domain.canonical import canonical_dumps

        payload = packet.model_dump(mode="json")
        existing = self.session.get(DecisionPacketRow, packet.identity.packet_id)
        if existing is not None:
            existing.packet_sha256 = packet.integrity.packet_sha256
            existing.issued_sha256 = existing.issued_sha256 or packet.integrity.packet_sha256
            existing.canonical_json = canonical_dumps(payload)
            existing.payload = payload
            existing.displayable = displayable
            existing.pre_issuance_event_id = self.pre_issuance_event_id
        else:
            self.session.add(
                DecisionPacketRow(
                    packet_id=packet.identity.packet_id,
                    case_id=packet.identity.case_id,
                    packet_version=packet.identity.packet_version,
                    route=packet.route.value,
                    packet_sha256=packet.integrity.packet_sha256,
                    issued_sha256=packet.integrity.packet_sha256,
                    canonical_json=canonical_dumps(payload),
                    payload=payload,
                    pre_issuance_event_id=self.pre_issuance_event_id,
                    displayable=displayable,
                    created_at=packet.identity.created_at,
                )
            )
        self.session.flush()


def process_case(
    session: Session,
    case: CaseRow,
    identity: IdentityAssertion,
    options: ProcessOptions | None = None,
) -> ProcessResult:
    return CaseProcessor(session, case, identity, options).run()


def normalise_question(raw: str) -> str:
    """Deterministic normalisation: collapse whitespace, strip, NFC via canonical helpers."""
    from app.domain.canonical import normalise_text

    collapsed = " ".join(normalise_text(raw).split())
    return collapsed


def question_digest(normalised: str) -> str:
    return text_sha256(normalised)


def build_case_row(
    *,
    case_id: str,
    identity: IdentityAssertion,
    raw_question: str,
    authorization_id: str,
    use_case_contract_id: str,
    submitted_at: datetime | None = None,
) -> CaseRow:
    normalised = normalise_question(raw_question)
    return CaseRow(
        case_id=case_id,
        requester_identity_id=identity.identity_id,
        business_scope_id=identity.business_scope_id,
        use_case_contract_id=use_case_contract_id,
        authorization_id=authorization_id,
        raw_question=raw_question,
        normalised_question=normalised,
        question_sha256=question_digest(normalised),
        current_state=CaseState.AUTHORIZATION_PREFLIGHT.value,
        submitted_at=submitted_at or utc_now(),
    )


__all__ = [
    "CONCURRENT_CASES_MAX",
    "DataClassification",
    "ProcessOptions",
    "ProcessResult",
    "StopError",
    "build_case_row",
    "normalise_question",
    "process_case",
    "question_digest",
]
