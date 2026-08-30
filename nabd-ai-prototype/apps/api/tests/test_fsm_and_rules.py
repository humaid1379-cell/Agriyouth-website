"""Slice 3: the state machine and the deterministic rule framework.

Rule vectors are table-driven: each row states an input context and the exact outcome,
reason code and effect the rule must produce.
"""

from __future__ import annotations

import pytest

from app.domain.canonical import utc_now
from app.domain.enums import (
    ORDERED_CASE_STATES,
    TERMINAL_CASE_STATES,
    CaseState,
    IdentityStatus,
    RuleEffect,
    RuleOutcome,
    SupportState,
)
from app.domain.errors import IllegalTransitionError
from app.domain.fsm import (
    DECLARED_TRANSITIONS,
    assert_transition,
    failure_reason_for,
    is_declared,
    next_state,
    transition_table,
)
from app.domain.reason_codes import ReasonCode
from app.rules import EXPECTED_RULE_IDS, REGISTRY, RuleContext, assert_catalog_loaded
from app.rules.catalog import catalog_payload
from app.schemas.model_io import VerificationResponse

pytestmark = pytest.mark.unit


class TestStateMachine:
    def test_catalog_of_declared_edges_is_closed(self) -> None:
        for from_state, to_state in DECLARED_TRANSITIONS:
            assert isinstance(from_state, CaseState)
            assert isinstance(to_state, CaseState)

    def test_every_sequential_edge_is_declared(self) -> None:
        for index in range(len(ORDERED_CASE_STATES) - 1):
            assert is_declared(ORDERED_CASE_STATES[index], ORDERED_CASE_STATES[index + 1])

    @pytest.mark.parametrize(
        ("from_state", "to_state"),
        [
            (CaseState.AUTHORIZATION_PREFLIGHT, CaseState.PACKET_ASSEMBLY),
            (CaseState.EVIDENCE_SUFFICIENCY, CaseState.REQUEST_NORMALIZATION),
            (CaseState.BOUNDED_DRAFT, CaseState.BOUNDED_DRAFT),
            (CaseState.ROUTE_DETERMINATION, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW),
            (CaseState.SOURCE_ELIGIBILITY, CaseState.INDEPENDENT_VERIFICATION),
        ],
    )
    def test_skips_reorders_and_replays_are_rejected(
        self, from_state: CaseState, to_state: CaseState
    ) -> None:
        with pytest.raises(IllegalTransitionError):
            assert_transition("CASE-t", from_state, to_state)

    @pytest.mark.parametrize("terminal", sorted(TERMINAL_CASE_STATES, key=lambda s: s.value))
    def test_terminal_states_have_no_outbound_edge(self, terminal: CaseState) -> None:
        for target in CaseState:
            with pytest.raises(IllegalTransitionError):
                assert_transition("CASE-t", terminal, target)

    def test_every_pre_human_state_can_stop(self) -> None:
        for state in ORDERED_CASE_STATES:
            if state is CaseState.CLOSED_DECISION_SUPPORT_RECORD:
                continue
            assert is_declared(state, CaseState.CANNOT_PROCEED)

    def test_review_failure_returns_to_waiting(self) -> None:
        assert is_declared(
            CaseState.REVIEWER_AUTHORITY_AND_SOD, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW
        )
        assert is_declared(
            CaseState.DISPOSITION_BINDING, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW
        )

    def test_next_state_follows_the_ordered_workflow(self) -> None:
        assert next_state(CaseState.AUTHORIZATION_PREFLIGHT) is (
            CaseState.ACTOR_AND_SESSION_VERIFICATION
        )

    def test_transition_table_lists_every_state(self) -> None:
        rows = transition_table()
        assert len(rows) == 21
        assert rows[-1]["state"] == CaseState.CANNOT_PROCEED.value
        assert rows[-1]["terminal"] is True

    def test_failure_reason_exists_for_each_processing_state(self) -> None:
        for state in ORDERED_CASE_STATES[:15]:
            assert isinstance(failure_reason_for(state), ReasonCode)


class TestRuleCatalog:
    def test_catalog_matches_the_frozen_expectation(self) -> None:
        assert_catalog_loaded()
        assert set(REGISTRY.ids()) == EXPECTED_RULE_IDS

    def test_precedence_is_unique_and_ordered(self) -> None:
        ranks = [rule.precedence_rank for rule in REGISTRY.all()]
        assert ranks == sorted(ranks)
        assert len(set(ranks)) == len(ranks)

    def test_kill_switch_and_prohibited_path_outrank_everything(self) -> None:
        assert REGISTRY.get("KILL-001").precedence_rank == 0
        assert REGISTRY.get("PATH-001").precedence_rank == 1

    def test_every_state_has_at_least_one_applicable_rule(self) -> None:
        for state in CaseState:
            assert REGISTRY.for_state(state), f"{state.value} has no applicable rule"

    def test_catalog_payload_is_machine_readable(self) -> None:
        payload = catalog_payload()
        assert len(payload) == len(EXPECTED_RULE_IDS)
        for entry in payload:
            assert entry["rule_version"]
            assert entry["purpose"]
            assert entry["evaluated_in_states"]


def _context(state: CaseState, **kwargs: object) -> RuleContext:
    from app.services.fixtures import contract_extras, load_use_case_contract, primary_authorization

    base: dict[str, object] = {
        "case_id": "CASE-vector",
        "state": state,
        "evaluated_at": utc_now(),
        "authorization": primary_authorization(),
        "contract": load_use_case_contract(),
        "contract_extras": contract_extras(),
    }
    base.update(kwargs)
    return RuleContext(**base)  # type: ignore[arg-type]


class TestRuleVectors:
    """Table-driven vectors. Each row pins the exact outcome, reason code and effect."""

    def test_kill_001_stops_when_active(self) -> None:
        rule = REGISTRY.get("KILL-001")
        blocked = rule.evaluate(_context(CaseState.REQUEST_NORMALIZATION, kill_switch_active=True))
        assert blocked.outcome is RuleOutcome.FAIL
        assert blocked.reason_code is ReasonCode.EMERGENCY_STOP_ACTIVE
        assert blocked.effect is RuleEffect.MANDATORY_STOP

        allowed = rule.evaluate(_context(CaseState.REQUEST_NORMALIZATION, kill_switch_active=False))
        assert allowed.outcome is RuleOutcome.PASS

    @pytest.mark.parametrize(
        ("kwargs", "expected_outcome"),
        [
            ({}, RuleOutcome.PASS),
            ({"configured_action_endpoints": ("https://ops/webhook",)}, RuleOutcome.FAIL),
            ({"attempted_action_path": "POST https://ops/approve"}, RuleOutcome.FAIL),
        ],
    )
    def test_path_001_blocks_any_action_path(
        self, kwargs: dict[str, object], expected_outcome: RuleOutcome
    ) -> None:
        result = REGISTRY.get("PATH-001").evaluate(_context(CaseState.PACKET_ASSEMBLY, **kwargs))
        assert result.outcome is expected_outcome
        if expected_outcome is RuleOutcome.FAIL:
            assert result.reason_code is ReasonCode.PROHIBITED_ACTION_PATH_DETECTED

    def test_auth_001_rejects_a_manifest_hash_it_does_not_admit(self) -> None:
        result = REGISTRY.get("AUTH-001").evaluate(
            _context(CaseState.AUTHORIZATION_PREFLIGHT, manifest_sha256="f" * 64)
        )
        assert result.outcome is RuleOutcome.FAIL
        assert result.reason_code is ReasonCode.MANIFEST_HASH_MISMATCH

    def test_auth_001_passes_for_the_frozen_manifest(self) -> None:
        from app.services.fixtures import load_corpus_fixtures

        result = REGISTRY.get("AUTH-001").evaluate(
            _context(
                CaseState.AUTHORIZATION_PREFLIGHT,
                manifest_sha256=load_corpus_fixtures().manifest_sha256,
            )
        )
        assert result.outcome is RuleOutcome.PASS

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (IdentityStatus.ACTIVE, RuleOutcome.PASS),
            (IdentityStatus.EXPIRED, RuleOutcome.FAIL),
            (IdentityStatus.REVOKED, RuleOutcome.FAIL),
            (IdentityStatus.UNKNOWN, RuleOutcome.FAIL),
        ],
    )
    def test_id_001_vectors(self, status: IdentityStatus, expected: RuleOutcome) -> None:
        from app.services.identity import assertion_for_fixture

        identity = assertion_for_fixture("requester.analyst@demo.nabd.local").model_copy(
            update={"status": status}
        )
        result = REGISTRY.get("ID-001").evaluate(
            _context(CaseState.ACTOR_AND_SESSION_VERIFICATION, identity=identity)
        )
        assert result.outcome is expected
        if expected is RuleOutcome.FAIL:
            assert result.effect is RuleEffect.DENY_WITHOUT_DISCLOSURE

    @pytest.mark.parametrize(
        ("question", "expected", "reason"),
        [
            (
                "What evidence must accompany an internal policy exception request?",
                RuleOutcome.PASS,
                None,
            ),
            ("short?", RuleOutcome.FAIL, ReasonCode.REQUEST_CONTRACT_INVALID),
            (
                "What is the review period? And who owns the register?",
                RuleOutcome.FAIL,
                ReasonCode.REQUEST_CONTRACT_INVALID,
            ),
            (
                "What is the review period for a Tier 2 request and also tell me the owner",
                RuleOutcome.FAIL,
                ReasonCode.REQUEST_CONTRACT_INVALID,
            ),
            ("x" * 2100, RuleOutcome.FAIL, ReasonCode.REQUEST_LIMIT_EXCEEDED),
        ],
    )
    def test_req_001_vectors(
        self, question: str, expected: RuleOutcome, reason: ReasonCode | None
    ) -> None:
        result = REGISTRY.get("REQ-001").evaluate(
            _context(CaseState.REQUEST_NORMALIZATION, normalised_question=question)
        )
        assert result.outcome is expected
        if reason is not None:
            assert result.reason_code is reason

    @pytest.mark.parametrize(
        ("question", "expected"),
        [
            ("What evidence must accompany an exception request", RuleOutcome.PASS),
            ("Please approve the Tier 2 exception request", RuleOutcome.FAIL),
            ("Send the confirmation email to the analyst", RuleOutcome.FAIL),
            ("Update the record in the exception register", RuleOutcome.FAIL),
            ("Grant access to the restricted records", RuleOutcome.FAIL),
        ],
    )
    def test_scope_001_vectors(self, question: str, expected: RuleOutcome) -> None:
        result = REGISTRY.get("SCOPE-001").evaluate(
            _context(CaseState.USE_CASE_AND_RISK_SCOPE, normalised_question=question)
        )
        assert result.outcome is expected
        if expected is RuleOutcome.FAIL:
            assert result.reason_code is ReasonCode.USE_CASE_EXCLUDED_OR_UNBOUNDED

    def test_src_001_stops_on_a_hash_mismatch(self) -> None:
        result = REGISTRY.get("SRC-001").evaluate(
            _context(CaseState.SOURCE_ELIGIBILITY, hash_mismatches=("POL-001@v1",))
        )
        assert result.outcome is RuleOutcome.FAIL
        assert result.reason_code is ReasonCode.MANIFEST_HASH_MISMATCH

    def test_src_001_stops_when_nothing_is_eligible(self) -> None:
        result = REGISTRY.get("SRC-001").evaluate(_context(CaseState.SOURCE_ELIGIBILITY))
        assert result.outcome is RuleOutcome.FAIL
        assert result.reason_code is ReasonCode.SOURCE_ELIGIBILITY_FAILURE

    def test_clm_001_rejects_a_citation_outside_the_admitted_set(self) -> None:
        verification = VerificationResponse(
            verified_claims=(
                {
                    "claim_ref": "C01",
                    "support_state": SupportState.SUPPORTED,
                    "evidence_ids": ("EXC-not-admitted",),
                    "support_spans": (),
                    "conflict_ids": (),
                },
            )
        )
        result = REGISTRY.get("CLM-001").evaluate(
            _context(CaseState.INDEPENDENT_VERIFICATION, verification=verification, excerpts=())
        )
        assert result.outcome is RuleOutcome.FAIL
        assert result.reason_code is ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED

    def test_clm_001_reports_material_claim_failures(self) -> None:
        result = REGISTRY.get("CLM-001").evaluate(
            _context(CaseState.INDEPENDENT_VERIFICATION, material_claim_failures=("C01",))
        )
        assert result.outcome is RuleOutcome.FAIL
        assert result.input_refs == ("C01",)

    @pytest.mark.parametrize(
        ("kwargs", "reason"),
        [
            ({"normalised_question": "x" * 2001}, ReasonCode.REQUEST_LIMIT_EXCEEDED),
            ({"retrieval_candidate_count": 13}, ReasonCode.RETRIEVAL_LIMIT_EXCEEDED),
            ({"total_context_chars": 8001}, ReasonCode.CONTEXT_LIMIT_EXCEEDED),
            ({"model_calls_used": 3}, ReasonCode.MODEL_CALL_LIMIT_EXCEEDED),
            ({"retries_used": 2}, ReasonCode.RETRY_LIMIT_EXCEEDED),
            ({"max_model_output_chars": 6001}, ReasonCode.MODEL_OUTPUT_LIMIT_EXCEEDED),
            ({"elapsed_seconds": 61}, ReasonCode.CASE_WALL_CLOCK_LIMIT_EXCEEDED),
            ({"concurrent_cases": 3}, ReasonCode.CONCURRENCY_LIMIT_EXCEEDED),
        ],
    )
    def test_lim_001_over_limit_vectors(
        self, kwargs: dict[str, object], reason: ReasonCode
    ) -> None:
        result = REGISTRY.get("LIM-001").evaluate(_context(CaseState.PACKET_ASSEMBLY, **kwargs))
        assert result.outcome is RuleOutcome.FAIL
        assert result.reason_code is reason

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"normalised_question": "x" * 2000},
            {"retrieval_candidate_count": 12},
            {"total_context_chars": 8000},
            {"model_calls_used": 2},
            {"retries_used": 1},
            {"max_model_output_chars": 6000},
            {"elapsed_seconds": 60},
            {"concurrent_cases": 2},
        ],
    )
    def test_lim_001_at_limit_is_permitted(self, kwargs: dict[str, object]) -> None:
        result = REGISTRY.get("LIM-001").evaluate(_context(CaseState.PACKET_ASSEMBLY, **kwargs))
        assert result.outcome is RuleOutcome.PASS

    def test_aud_001_requires_distinct_critical_events(self) -> None:
        rule = REGISTRY.get("AUD-001")
        missing = rule.evaluate(_context(CaseState.PACKET_PRE_ISSUANCE_AUDIT))
        assert missing.outcome is RuleOutcome.FAIL
        assert missing.reason_code is ReasonCode.CRITICAL_AUDIT_FAILURE

        same = rule.evaluate(
            _context(
                CaseState.DISPOSITION_CLOSURE_AUDIT,
                confirmed_pre_issuance_event_id="EVT-1",
                confirmed_closure_event_id="EVT-1",
            )
        )
        assert same.outcome is RuleOutcome.FAIL

        distinct = rule.evaluate(
            _context(
                CaseState.DISPOSITION_CLOSURE_AUDIT,
                confirmed_pre_issuance_event_id="EVT-1",
                confirmed_closure_event_id="EVT-2",
            )
        )
        assert distinct.outcome is RuleOutcome.PASS

    def test_sod_001_reports_self_review_before_role(self) -> None:
        result = REGISTRY.get("SOD-001").evaluate(
            _context(
                CaseState.REVIEWER_AUTHORITY_AND_SOD,
                reviewer_identity_id="requester.analyst@demo.nabd.local",
                requester_identity_id="requester.analyst@demo.nabd.local",
                reviewer_role_id="ROLE_SYNTHETIC_REQUESTER_V1",
                reviewer_status="ACTIVE",
                reviewer_scope_id="BUSINESS_UNIT_V1",
            )
        )
        assert result.outcome is RuleOutcome.FAIL
        assert result.reason_code is ReasonCode.SEPARATION_OF_DUTIES_VIOLATION

    @pytest.mark.parametrize(
        ("kwargs", "reason"),
        [
            ({"reviewer_status": "REVOKED"}, ReasonCode.REVIEWER_AUTHORITY_INVALID),
            ({"reviewer_role_id": "ROLE_SYNTHETIC_REQUESTER_V1"}, ReasonCode.REVIEWER_AUTHORITY_INVALID),
            ({"reviewer_scope_id": "BUSINESS_UNIT_FIELD_OPS"}, ReasonCode.ACCESS_DENIED),
        ],
    )
    def test_sod_001_authority_vectors(
        self, kwargs: dict[str, object], reason: ReasonCode
    ) -> None:
        base: dict[str, object] = {
            "reviewer_identity_id": "reviewer.manager@demo.nabd.local",
            "requester_identity_id": "requester.analyst@demo.nabd.local",
            "reviewer_role_id": "ROLE_SYNTHETIC_REVIEWER_V1",
            "reviewer_status": "ACTIVE",
            "reviewer_scope_id": "BUSINESS_UNIT_V1",
        }
        base.update(kwargs)
        result = REGISTRY.get("SOD-001").evaluate(
            _context(CaseState.REVIEWER_AUTHORITY_AND_SOD, **base)
        )
        assert result.outcome is RuleOutcome.FAIL
        assert result.reason_code is reason

    def test_sod_001_requires_a_substantive_rationale_at_binding(self) -> None:
        base: dict[str, object] = {
            "reviewer_identity_id": "reviewer.manager@demo.nabd.local",
            "requester_identity_id": "requester.analyst@demo.nabd.local",
            "reviewer_role_id": "ROLE_SYNTHETIC_REVIEWER_V1",
            "reviewer_status": "ACTIVE",
            "reviewer_scope_id": "BUSINESS_UNIT_V1",
        }
        blank = REGISTRY.get("SOD-001").evaluate(
            _context(CaseState.DISPOSITION_BINDING, disposition_rationale="   ", **base)
        )
        assert blank.outcome is RuleOutcome.FAIL
        assert blank.reason_code is ReasonCode.DISPOSITION_RATIONALE_REQUIRED

        substantive = REGISTRY.get("SOD-001").evaluate(
            _context(
                CaseState.DISPOSITION_BINDING,
                disposition_rationale="Checked the citations against the claim ledger.",
                **base,
            )
        )
        assert substantive.outcome is RuleOutcome.PASS
