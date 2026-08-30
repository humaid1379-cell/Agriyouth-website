"""Slices 6 and 7: claims, verification, routing, packet issuance, dual audit and review."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.protocol import ModelFault
from app.domain.canonical import verify_packet_hash
from app.domain.enums import (
    AuditEventType,
    AuthorizationStatus,
    CaseState,
    DispositionValue,
    Materiality,
    OperationalStatus,
    Route,
    Severity,
    StatusEvidence,
    SupportState,
)
from app.domain.errors import AccessDeniedError, ControlError, StopError
from app.domain.notices import REQUIRED_NOTICE_IDS
from app.domain.reason_codes import ReasonCode
from app.repositories.tables import (
    AuditEventRow,
    CaseStateTransitionRow,
    DecisionPacketRow,
    HumanDispositionRow,
)
from app.services import audit
from app.services.orchestrator import ProcessOptions, process_case
from app.services.packet import SemanticContext, validate_packet_semantics
from app.services.review import displayable_packet, review_queue, submit_disposition

pytestmark = pytest.mark.integration

CONFLICT_QUESTION = (
    "Within how many business days must a reviewer complete an exception review where the "
    "exception file affects access to restricted records?"
)
ACTION_QUESTION = (
    "Please approve the Tier 2 exception request for the Corporate Services Unit and send "
    "the confirmation email to the requesting analyst."
)


class TestHappyPath:
    def test_benign_case_reaches_awaiting_review_with_a_sealed_packet(
        self, processed_case
    ) -> None:
        case, result = processed_case
        assert result.terminal_state is CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW
        assert result.route is Route.HUMAN_REVIEW_REQUIRED
        assert result.reason_code is None
        assert result.packet is not None
        assert verify_packet_hash(result.packet.model_dump(mode="json"))

    def test_exactly_two_model_calls_are_made(self, processed_case) -> None:
        _, result = processed_case
        assert result.model_calls == 2

    def test_every_material_claim_is_supported_with_a_verified_quote(self, processed_case) -> None:
        _, result = processed_case
        material = [c for c in result.claims if c.materiality is Materiality.MATERIAL]
        assert material
        for claim in material:
            assert claim.support_state is SupportState.SUPPORTED
            assert claim.evidence_links
            assert all(link.quote_verified for link in claim.evidence_links)

    def test_citations_resolve_to_admitted_excerpts(self, processed_case) -> None:
        _, result = processed_case
        admitted = {e.excerpt_id for e in result.excerpts}
        for claim in result.claims:
            for link in claim.evidence_links:
                assert link.excerpt_id in admitted

    def test_packet_carries_all_four_fixed_notices_and_four_status_dimensions(
        self, processed_case
    ) -> None:
        _, result = processed_case
        packet = result.packet
        assert packet is not None
        assert {n.notice_id for n in packet.notices} == REQUIRED_NOTICE_IDS
        assert packet.prototype_status.built is StatusEvidence.NOT_EVIDENCED
        assert packet.prototype_status.integration is StatusEvidence.NOT_EVIDENCED
        assert packet.prototype_status.operational is OperationalStatus.NOT_EVIDENCED
        assert packet.prototype_status.authorization is AuthorizationStatus.NOT_GRANTED

    def test_packet_records_full_version_lineage(self, processed_case) -> None:
        _, result = processed_case
        lineage = result.packet.version_lineage  # type: ignore[union-attr]
        assert lineage.corpus_version == "synthetic_policy_collection_v1"
        assert lineage.canonical_json_profile == "nabd-canonical-json-v1"
        assert lineage.draft_model_configuration_id == "MC-MOCK-DRAFTER-V1"
        assert lineage.verifier_model_configuration_id == "MC-MOCK-VERIFIER-V1"

    def test_every_state_transition_is_recorded_in_order(
        self, db: Session, processed_case
    ) -> None:
        case, _ = processed_case
        rows = db.execute(
            select(CaseStateTransitionRow)
            .where(CaseStateTransitionRow.case_id == case.case_id)
            .order_by(CaseStateTransitionRow.sequence)
        ).scalars().all()
        assert [row.sequence for row in rows] == list(range(1, len(rows) + 1))
        assert rows[-1].to_state == CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW.value

    def test_semantic_validation_passes_for_the_issued_packet(
        self, db: Session, processed_case
    ) -> None:
        case, result = processed_case
        from app.services.fixtures import primary_authorization

        failures = validate_packet_semantics(
            result.packet,  # type: ignore[arg-type]
            SemanticContext(
                case_id=case.case_id,
                authorization=primary_authorization(),
                eligible_source_keys=frozenset(
                    f"{e.source_id}@{e.source_version}" for e in result.excerpts
                ),
                admitted_excerpt_ids=frozenset(e.excerpt_id for e in result.excerpts),
                issued_packet_sha256=result.packet.integrity.packet_sha256,  # type: ignore[union-attr]
                confirmed_pre_issuance_event_id=result.pre_issuance_event_id,
            ),
        )
        assert failures == ()


class TestStopPaths:
    @pytest.mark.parametrize(
        ("question", "expected"),
        [
            (ACTION_QUESTION, ReasonCode.USE_CASE_EXCLUDED_OR_UNBOUNDED),
            (
                "What is the review period? And who owns the exception register?",
                ReasonCode.REQUEST_CONTRACT_INVALID,
            ),
            (CONFLICT_QUESTION, ReasonCode.EVIDENCE_INSUFFICIENT_OR_CONFLICTED),
        ],
    )
    def test_request_and_evidence_stops(
        self, db: Session, make_case, requester_identity, question: str, expected: ReasonCode
    ) -> None:
        case = make_case(requester_identity, question)
        result = process_case(db, case, requester_identity)
        assert result.route is Route.CANNOT_PROCEED
        assert result.reason_code == expected.value
        assert result.packet is None
        assert result.model_calls == 0

    @pytest.mark.parametrize(
        ("options", "expected"),
        [
            (
                ProcessOptions(fault=ModelFault.DRAFT_MALFORMED),
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
            ),
            (
                ProcessOptions(fault=ModelFault.VERIFIER_TIMEOUT),
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
            ),
            (
                ProcessOptions(fault=ModelFault.FABRICATED_CITATION),
                ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
            ),
            (
                ProcessOptions(fault=ModelFault.PARTIAL_SUPPORT),
                ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
            ),
            (
                ProcessOptions(fault=ModelFault.VERIFIER_DISAGREEMENT),
                ReasonCode.MATERIAL_CLAIM_UNSUPPORTED_OR_CONFLICTED,
            ),
            (
                ProcessOptions(attempt_third_model_call=True),
                ReasonCode.MODEL_CALL_LIMIT_EXCEEDED,
            ),
            (
                ProcessOptions(simulate_hash_mismatch=True),
                ReasonCode.MANIFEST_HASH_MISMATCH,
            ),
            (
                ProcessOptions(skip_pre_issuance_audit=True),
                ReasonCode.CRITICAL_AUDIT_FAILURE,
            ),
            (
                ProcessOptions(attempted_action_path="POST https://ops.example/webhook"),
                ReasonCode.PROHIBITED_ACTION_PATH_DETECTED,
            ),
            (
                ProcessOptions(omit_rule_id="CLM-001"),
                ReasonCode.DETERMINISTIC_GOVERNANCE_FAILURE,
            ),
            (
                ProcessOptions(simulate_elapsed_seconds=61),
                ReasonCode.CASE_WALL_CLOCK_LIMIT_EXCEEDED,
            ),
        ],
    )
    def test_control_failures_fail_closed(
        self,
        db: Session,
        make_case,
        requester_identity,
        benign_question: str,
        options: ProcessOptions,
        expected: ReasonCode,
    ) -> None:
        case = make_case(requester_identity, benign_question)
        result = process_case(db, case, requester_identity, options)
        assert result.route is Route.CANNOT_PROCEED
        assert result.reason_code == expected.value
        assert result.packet is None
        assert result.stop_record is not None
        assert result.stop_record.failed_state

    def test_no_packet_row_is_displayable_after_a_stop(
        self, db: Session, make_case, requester_identity, benign_question: str
    ) -> None:
        case = make_case(requester_identity, benign_question)
        process_case(
            db, case, requester_identity, ProcessOptions(skip_pre_issuance_audit=True)
        )
        rows = db.execute(
            select(DecisionPacketRow).where(DecisionPacketRow.case_id == case.case_id)
        ).scalars().all()
        assert rows == []

    def test_expired_identity_is_denied_without_case_content(
        self, db: Session, make_case
    ) -> None:
        from app.services.identity import assertion_for_fixture

        expired = assertion_for_fixture("expired.requester@demo.nabd.local")
        case = make_case(expired)
        result = process_case(db, case, expired)
        assert result.reason_code == ReasonCode.REQUESTER_OR_SESSION_INVALID.value
        assert result.excerpts == ()
        assert result.model_calls == 0

    def test_kill_switch_halts_processing(
        self, db: Session, make_case, requester_identity, admin_identity, benign_question: str
    ) -> None:
        from app.services.kill_switch import set_kill_switch

        set_kill_switch(
            db,
            active=True,
            actor_id=admin_identity.identity_id,
            reason="Test exercising the emergency stop.",
        )
        case = make_case(requester_identity, benign_question)
        result = process_case(db, case, requester_identity)
        assert result.reason_code == ReasonCode.EMERGENCY_STOP_ACTIVE.value
        assert result.model_calls == 0

    def test_at_limit_wall_clock_still_completes(
        self, db: Session, make_case, requester_identity, benign_question: str
    ) -> None:
        case = make_case(requester_identity, benign_question)
        result = process_case(
            db, case, requester_identity, ProcessOptions(simulate_elapsed_seconds=60)
        )
        assert result.route is Route.HUMAN_REVIEW_REQUIRED


class TestAuditChain:
    def test_chain_verifies_after_a_full_run(self, db: Session, processed_case) -> None:
        case, _ = processed_case
        verification = audit.verify_chain(db, case.case_id)
        assert verification.verified is True
        assert verification.event_count > 0

    def test_chain_links_each_event_to_its_predecessor(
        self, db: Session, processed_case
    ) -> None:
        case, _ = processed_case
        rows = audit.load_chain(db, case.case_id)
        assert rows[0].previous_event_hash == "0" * 64
        for previous, current in zip(rows, rows[1:], strict=False):
            assert current.previous_event_hash == previous.event_hash

    def test_tampering_with_a_stored_event_is_detected(
        self, db: Session, processed_case
    ) -> None:
        case, _ = processed_case
        rows = audit.load_chain(db, case.case_id)
        target = rows[len(rows) // 2]
        payload = dict(target.payload)
        payload["outcome"] = "FAIL"
        # The append-only trigger blocks UPDATE, so tamper detection is exercised against a
        # detached copy of the stored payload rather than by mutating the row.
        from app.schemas.audit import AuditEvent

        tampered = AuditEvent.model_validate(payload)
        assert tampered.hash_matches() is False

    def test_confirmed_pre_issuance_event_binds_the_issued_hash(
        self, db: Session, processed_case
    ) -> None:
        case, result = processed_case
        confirmed = audit.find_confirmed(db, case.case_id, AuditEventType.PACKET_PRE_ISSUANCE)
        assert confirmed is not None
        binding = confirmed.payload["binding"]
        assert binding["object_sha256"] == result.packet.integrity.packet_sha256  # type: ignore[union-attr]

    def test_audit_rows_cannot_be_updated_or_deleted(
        self, db: Session, processed_case
    ) -> None:
        from sqlalchemy import delete, text, update

        case, _ = processed_case
        db.commit()
        with pytest.raises(Exception, match="append-only"):
            db.execute(
                update(AuditEventRow)
                .where(AuditEventRow.case_id == case.case_id)
                .values(outcome="FAIL")
            )
            db.flush()
        db.rollback()
        with pytest.raises(Exception, match="append-only"):
            db.execute(delete(AuditEventRow).where(AuditEventRow.case_id == case.case_id))
            db.flush()
        db.rollback()
        assert db.execute(text("SELECT 1")).scalar() == 1

    def test_security_events_are_recorded_for_quarantined_sources(
        self, db: Session, processed_case
    ) -> None:
        case, _ = processed_case
        events = [
            row
            for row in audit.load_chain(db, case.case_id)
            if row.event_type == AuditEventType.SECURITY_EVENT.value
        ]
        assert events
        assert any(row.reason_code == ReasonCode.SOURCE_QUARANTINED.value for row in events)


class TestReviewAndDisposition:
    def test_reviewer_can_accept_as_test_evidence(
        self, db: Session, processed_case, reviewer_identity, valid_rationale: str
    ) -> None:
        case, _ = processed_case
        outcome = submit_disposition(
            db,
            case=case,
            identity=reviewer_identity,
            disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
            rationale=valid_rationale,
        )
        assert outcome.is_final is True
        assert outcome.terminal_state is CaseState.CLOSED_DECISION_SUPPORT_RECORD
        assert "does not approve, execute, transmit, or activate" in (
            outcome.disposition.non_execution_notice
        )

    def test_closure_requires_a_distinct_later_confirmed_event(
        self, db: Session, processed_case, reviewer_identity, valid_rationale: str
    ) -> None:
        case, _ = processed_case
        submit_disposition(
            db,
            case=case,
            identity=reviewer_identity,
            disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
            rationale=valid_rationale,
        )
        pre = audit.find_confirmed(db, case.case_id, AuditEventType.PACKET_PRE_ISSUANCE)
        closure = audit.find_confirmed(db, case.case_id, AuditEventType.DISPOSITION_CLOSURE)
        assert pre is not None and closure is not None
        assert pre.event_id != closure.event_id
        assert closure.sequence > pre.sequence

    def test_requester_cannot_review_its_own_case(
        self, db: Session, processed_case, requester_identity, valid_rationale: str
    ) -> None:
        case, _ = processed_case
        with pytest.raises(ControlError) as excinfo:
            submit_disposition(
                db,
                case=case,
                identity=requester_identity,
                disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
                rationale=valid_rationale,
            )
        assert excinfo.value.code is ReasonCode.SEPARATION_OF_DUTIES_VIOLATION
        db.refresh(case)
        assert case.current_state == CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW.value

    def test_blank_rationale_binds_nothing(
        self, db: Session, processed_case, reviewer_identity
    ) -> None:
        case, _ = processed_case
        with pytest.raises(ControlError) as excinfo:
            submit_disposition(
                db,
                case=case,
                identity=reviewer_identity,
                disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
                rationale="   ",
            )
        assert excinfo.value.code is ReasonCode.DISPOSITION_RATIONALE_REQUIRED
        assert (
            db.execute(
                select(HumanDispositionRow).where(HumanDispositionRow.case_id == case.case_id)
            ).scalars().all()
            == []
        )

    def test_revoked_reviewer_is_denied(
        self, db: Session, processed_case, valid_rationale: str
    ) -> None:
        from app.services.identity import assertion_for_fixture

        case, _ = processed_case
        revoked = assertion_for_fixture("revoked.reviewer@demo.nabd.local")
        with pytest.raises(ControlError) as excinfo:
            submit_disposition(
                db,
                case=case,
                identity=revoked,
                disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
                rationale=valid_rationale,
            )
        assert excinfo.value.code is ReasonCode.REVIEWER_AUTHORITY_INVALID

    def test_cross_scope_reviewer_is_denied(
        self, db: Session, processed_case, valid_rationale: str
    ) -> None:
        from app.services.identity import assertion_for_fixture

        case, _ = processed_case
        outsider = assertion_for_fixture("crossscope.reviewer@demo.nabd.local")
        with pytest.raises(ControlError) as excinfo:
            submit_disposition(
                db,
                case=case,
                identity=outsider,
                disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
                rationale=valid_rationale,
            )
        assert excinfo.value.code is ReasonCode.ACCESS_DENIED

    def test_return_for_clarification_keeps_the_case_open(
        self, db: Session, processed_case, reviewer_identity, valid_rationale: str
    ) -> None:
        case, _ = processed_case
        outcome = submit_disposition(
            db,
            case=case,
            identity=reviewer_identity,
            disposition_value=DispositionValue.RETURN_FOR_CLARIFICATION,
            rationale=valid_rationale,
        )
        assert outcome.is_final is False
        assert outcome.terminal_state is CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW

    def test_a_second_final_disposition_is_refused(
        self, db: Session, processed_case, reviewer_identity, valid_rationale: str
    ) -> None:
        case, _ = processed_case
        submit_disposition(
            db,
            case=case,
            identity=reviewer_identity,
            disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
            rationale=valid_rationale,
        )
        with pytest.raises(ControlError):
            submit_disposition(
                db,
                case=case,
                identity=reviewer_identity,
                disposition_value=DispositionValue.REJECT_AS_TEST_EVIDENCE,
                rationale=valid_rationale,
            )

    def test_reviewer_queue_excludes_own_requests(
        self, db: Session, processed_case, reviewer_identity, requester_identity
    ) -> None:
        queue = review_queue(db, reviewer_identity)
        assert all(row.requester_identity_id != reviewer_identity.identity_id for row in queue)
        assert any(row.requester_identity_id == requester_identity.identity_id for row in queue)

    def test_requester_cannot_open_the_review_queue(
        self, db: Session, requester_identity
    ) -> None:
        with pytest.raises(AccessDeniedError):
            review_queue(db, requester_identity)

    def test_packet_is_undisplayable_without_a_confirmed_pre_issuance_event(
        self, db: Session, make_case, requester_identity, benign_question: str
    ) -> None:
        case = make_case(requester_identity, benign_question)
        process_case(
            db, case, requester_identity, ProcessOptions(skip_pre_issuance_audit=True)
        )
        with pytest.raises(ControlError):
            displayable_packet(db, case.case_id)

    def test_disposition_binds_the_exact_issued_hash(
        self, db: Session, processed_case, reviewer_identity, valid_rationale: str
    ) -> None:
        case, result = processed_case
        issued = result.packet.integrity.packet_sha256  # type: ignore[union-attr]
        outcome = submit_disposition(
            db,
            case=case,
            identity=reviewer_identity,
            disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
            rationale=valid_rationale,
            expected_packet_sha256=issued,
        )
        assert outcome.disposition.packet_sha256 == issued

    def test_a_stale_packet_hash_is_refused(
        self, db: Session, processed_case, reviewer_identity, valid_rationale: str
    ) -> None:
        case, _ = processed_case
        with pytest.raises(StopError):
            submit_disposition(
                db,
                case=case,
                identity=reviewer_identity,
                disposition_value=DispositionValue.ACCEPT_AS_TEST_EVIDENCE,
                rationale=valid_rationale,
                expected_packet_sha256="0" * 64,
            )


class TestReplayDeterminism:
    def test_identical_input_produces_identical_claims_and_route(
        self, db: Session, make_case, requester_identity, benign_question: str
    ) -> None:
        first = process_case(db, make_case(requester_identity, benign_question), requester_identity)
        second = process_case(
            db, make_case(requester_identity, benign_question), requester_identity
        )
        assert first.route is second.route
        assert [(c.claim_ref, c.statement, c.support_state) for c in first.claims] == [
            (c.claim_ref, c.statement, c.support_state) for c in second.claims
        ]

    def test_replayed_citations_are_identical(
        self, db: Session, make_case, requester_identity, benign_question: str
    ) -> None:
        first = process_case(db, make_case(requester_identity, benign_question), requester_identity)
        second = process_case(
            db, make_case(requester_identity, benign_question), requester_identity
        )
        assert [
            (link.source_id, link.page_number, link.quoted_text)
            for claim in first.claims
            for link in claim.evidence_links
        ] == [
            (link.source_id, link.page_number, link.quoted_text)
            for claim in second.claims
            for link in claim.evidence_links
        ]

    def test_both_replay_chains_verify(
        self, db: Session, make_case, requester_identity, benign_question: str
    ) -> None:
        first = process_case(db, make_case(requester_identity, benign_question), requester_identity)
        second = process_case(
            db, make_case(requester_identity, benign_question), requester_identity
        )
        assert audit.verify_chain(db, first.case_id).verified
        assert audit.verify_chain(db, second.case_id).verified


class TestPacketSemanticInvariants:
    def _context(self, case_id: str, result) -> SemanticContext:  # type: ignore[no-untyped-def]
        from app.services.fixtures import primary_authorization

        return SemanticContext(
            case_id=case_id,
            authorization=primary_authorization(),
            eligible_source_keys=frozenset(
                f"{e.source_id}@{e.source_version}" for e in result.excerpts
            ),
            admitted_excerpt_ids=frozenset(e.excerpt_id for e in result.excerpts),
            issued_packet_sha256=result.packet.integrity.packet_sha256,
            confirmed_pre_issuance_event_id=result.pre_issuance_event_id,
        )

    def test_case_id_mismatch_is_detected(self, processed_case) -> None:
        from app.schemas.packet import DecisionReadinessPacket

        case, result = processed_case
        payload = result.packet.model_dump(mode="json")
        payload["identity"]["case_id"] = "CASE-other"
        failures = validate_packet_semantics(
            DecisionReadinessPacket.model_validate(payload), self._context(case.case_id, result)
        )
        assert "SEM-01_CASE_ID_MISMATCH" in failures

    def test_altered_notice_text_is_detected(self, processed_case) -> None:
        from app.schemas.packet import DecisionReadinessPacket

        case, result = processed_case
        payload = result.packet.model_dump(mode="json")
        payload["notices"][0]["text_en"] = "This packet approves the request."
        failures = validate_packet_semantics(
            DecisionReadinessPacket.model_validate(payload), self._context(case.case_id, result)
        )
        assert "SEM-08_NOTICE_TEXT_ALTERED" in failures

    def test_an_unauthorized_component_version_is_detected(self, processed_case) -> None:
        from app.schemas.packet import DecisionReadinessPacket

        case, result = processed_case
        payload = result.packet.model_dump(mode="json")
        payload["version_lineage"]["rule_catalog_version"] = "rule-catalog-v9.9.9"
        failures = validate_packet_semantics(
            DecisionReadinessPacket.model_validate(payload), self._context(case.case_id, result)
        )
        assert any(f.startswith("SEM-05_VERSION_NOT_AUTHORIZED") for f in failures)

    def test_a_broken_seal_is_detected(self, processed_case) -> None:
        from app.schemas.packet import DecisionReadinessPacket

        case, result = processed_case
        payload = result.packet.model_dump(mode="json")
        payload["integrity"]["packet_sha256"] = "f" * 64
        failures = validate_packet_semantics(
            DecisionReadinessPacket.model_validate(payload), self._context(case.case_id, result)
        )
        assert "SEM-12_SEAL_DOES_NOT_VERIFY" in failures

    def test_a_citation_outside_the_admitted_set_is_detected(self, processed_case) -> None:
        from app.schemas.packet import DecisionReadinessPacket
        from app.services.fixtures import primary_authorization

        case, result = processed_case
        packet = DecisionReadinessPacket.model_validate(result.packet.model_dump(mode="json"))
        failures = validate_packet_semantics(
            packet,
            SemanticContext(
                case_id=case.case_id,
                authorization=primary_authorization(),
                eligible_source_keys=frozenset(
                    f"{e.source_id}@{e.source_version}" for e in result.excerpts
                ),
                admitted_excerpt_ids=frozenset(),
                issued_packet_sha256=packet.integrity.packet_sha256,
                confirmed_pre_issuance_event_id=result.pre_issuance_event_id,
            ),
        )
        assert "SEM-03_EXCERPT_NOT_ADMITTED" in failures

    def test_risk_uses_a_dominant_factor(self, processed_case) -> None:
        _, result = processed_case
        risk = result.packet.risk  # type: ignore[union-attr]
        assert risk.method == "dominant-factor-v1"
        dominant = next(f for f in risk.factors if f.factor_id == risk.dominant_factor_id)
        assert dominant.level is risk.inherent_risk


class TestSeverityRecording:
    def test_prohibited_action_path_records_an_s0_critical_event(
        self, db: Session, make_case, requester_identity, benign_question: str
    ) -> None:
        case = make_case(requester_identity, benign_question)
        process_case(
            db,
            case,
            requester_identity,
            ProcessOptions(attempted_action_path="POST https://ops.example/webhook"),
        )
        events = [
            row
            for row in audit.load_chain(db, case.case_id)
            if row.severity == Severity.S0_CRITICAL.value
        ]
        assert events
