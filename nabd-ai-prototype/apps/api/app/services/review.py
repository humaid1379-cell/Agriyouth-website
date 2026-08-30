"""Human review: reviewer authority, separation of duties, disposition binding, closure.

Review is an authority process, not a button (INV-11). Every disposition is re-checked
against the server-derived reviewer identity, the exact packet version and hash, and a
substantive human rationale, and it closes only after a distinct, later confirmed audit
event.

No disposition value reaches a connector, workflow, write, message, approval or
transaction (INV-12). The only effects of a disposition are database rows and audit
events inside this prototype.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.canonical import utc_now
from app.domain.enums import (
    FINAL_DISPOSITIONS,
    AuditEventType,
    AuditOutcome,
    CaseState,
    DemoRole,
    DispositionValue,
    Route,
    Severity,
)
from app.domain.errors import AccessDeniedError, ControlError, NotFoundError, StopError
from app.domain.fsm import assert_transition
from app.domain.ids import derived_id
from app.domain.reason_codes import ReasonCode
from app.domain.versions import COMPONENT_VERSIONS
from app.repositories.tables import (
    CaseRow,
    CaseStateTransitionRow,
    DecisionPacketRow,
    HumanDispositionRow,
)
from app.rules import RuleContext, assert_catalog_loaded, evaluate_state, first_mandatory_stop
from app.schemas.audit import ObjectBinding
from app.schemas.governance import IdentityAssertion
from app.schemas.packet import DecisionReadinessPacket, HumanDisposition
from app.services import audit
from app.services.fixtures import primary_authorization
from app.services.kill_switch import kill_switch_active
from app.services.packet import SemanticContext, validate_packet_semantics, with_audit_binding

REVIEW_SERVICE_ID = "service:human-review"


@dataclass(frozen=True, slots=True)
class DispositionOutcome:
    case_id: str
    disposition: HumanDisposition
    packet: DecisionReadinessPacket
    terminal_state: CaseState
    closure_event_id: str
    is_final: bool


def _record_transition(
    session: Session, case: CaseRow, target: CaseState, reason: ReasonCode | None, actor_id: str
) -> None:
    current = CaseState(case.current_state)
    assert_transition(case.case_id, current, target)
    sequence = (
        int(
            session.execute(
                select(CaseStateTransitionRow.sequence)
                .where(CaseStateTransitionRow.case_id == case.case_id)
                .order_by(CaseStateTransitionRow.sequence.desc())
            )
            .scalars()
            .first()
            or 0
        )
        + 1
    )
    session.add(
        CaseStateTransitionRow(
            transition_id=derived_id("event", case.case_id, f"t{sequence}"),
            case_id=case.case_id,
            sequence=sequence,
            from_state=current.value,
            to_state=target.value,
            reason_code=reason.value if reason else None,
            actor_id=actor_id,
            actor_kind="HUMAN_DEMO_IDENTITY",
            component_versions=dict(COMPONENT_VERSIONS),
            applicable_rule_versions=["SOD-001@1.0.0", "AUD-001@1.0.0"],
            occurred_at=utc_now(),
        )
    )
    audit.record(
        session,
        event_type=AuditEventType.STATE_TRANSITION,
        actor_id=actor_id,
        actor_kind="HUMAN_DEMO_IDENTITY",
        outcome=AuditOutcome.PASS if reason is None else AuditOutcome.FAIL,
        case_id=case.case_id,
        from_state=current,
        to_state=target,
        reason_code=reason.value if reason else None,
    )
    case.current_state = target.value
    case.updated_at = utc_now()
    session.flush()


def displayable_packet(session: Session, case_id: str) -> DecisionPacketRow:
    """Return the current displayable packet, or refuse.

    A packet is displayable only when a confirmed ``PACKET_PRE_ISSUANCE`` event exists whose
    binding matches the packet id, version and hash exactly. The stored ``displayable`` flag
    is not trusted on its own.
    """
    row = (
        session.execute(
            select(DecisionPacketRow)
            .where(DecisionPacketRow.case_id == case_id)
            .order_by(DecisionPacketRow.packet_version.desc())
        )
        .scalars()
        .first()
    )
    if row is None:
        raise NotFoundError(ReasonCode.PACKET_NOT_AVAILABLE, case_id=case_id)

    confirmed = audit.find_confirmed(session, case_id, AuditEventType.PACKET_PRE_ISSUANCE)
    if confirmed is None:
        raise StopError(ReasonCode.CRITICAL_AUDIT_FAILURE, case_id=case_id)
    binding = (confirmed.payload or {}).get("binding") or {}
    # The event binds the hash as sealed at pre-issuance. The packet's current hash differs
    # once a disposition is attached, so the issued hash is the correct comparand.
    if (
        binding.get("object_id") != row.packet_id
        or binding.get("object_version") != str(row.packet_version)
        or binding.get("object_sha256") != (row.issued_sha256 or row.packet_sha256)
    ):
        raise StopError(ReasonCode.CRITICAL_AUDIT_FAILURE, case_id=case_id)
    return row


def review_queue(session: Session, identity: IdentityAssertion) -> list[CaseRow]:
    """Cases awaiting review that this reviewer is eligible to see."""
    if identity.role is not DemoRole.REVIEWER:
        raise AccessDeniedError(ReasonCode.ACCESS_DENIED)
    rows = (
        session.execute(
            select(CaseRow)
            .where(CaseRow.current_state == CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW.value)
            .where(CaseRow.business_scope_id == identity.business_scope_id)
            .order_by(CaseRow.submitted_at.desc())
        )
        .scalars()
        .all()
    )
    # Separation of duties applies to the queue as well as to the action: a reviewer never
    # sees a case it requested.
    return [row for row in rows if row.requester_identity_id != identity.identity_id]


def _authority_context(
    session: Session, case: CaseRow, identity: IdentityAssertion, *, rationale: str | None
) -> RuleContext:
    return RuleContext(
        case_id=case.case_id,
        state=CaseState(case.current_state),
        authorization=primary_authorization(),
        identity=identity,
        reviewer_identity_id=identity.identity_id,
        reviewer_role_id=identity.role_id,
        reviewer_scope_id=identity.business_scope_id,
        reviewer_status=identity.status.value,
        requester_identity_id=case.requester_identity_id,
        disposition_rationale=rationale,
        kill_switch_active=kill_switch_active(session),
    )


def submit_disposition(
    session: Session,
    *,
    case: CaseRow,
    identity: IdentityAssertion,
    disposition_value: DispositionValue,
    rationale: str,
    expected_packet_sha256: str | None = None,
) -> DispositionOutcome:
    """Run stages 16 to 19. Any failure leaves the packet undisposed and waiting."""
    assert_catalog_loaded()

    if CaseState(case.current_state) is not CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW:
        raise StopError(
            ReasonCode.PACKET_NOT_AVAILABLE,
            case_id=case.case_id,
            state=CaseState(case.current_state),
        )

    packet_row = displayable_packet(session, case.case_id)
    packet = DecisionReadinessPacket.model_validate(packet_row.payload)
    issued_sha256 = packet_row.issued_sha256 or packet_row.packet_sha256

    audit.record(
        session,
        event_type=AuditEventType.REVIEW_ATTEMPT,
        actor_id=identity.identity_id,
        actor_kind="HUMAN_DEMO_IDENTITY",
        outcome=AuditOutcome.RECORDED,
        case_id=case.case_id,
        binding=ObjectBinding(
            object_kind="decision_packet",
            object_id=packet_row.packet_id,
            object_version=str(packet_row.packet_version),
            object_sha256=issued_sha256,
        ),
    )

    # Stage 16 - REVIEWER_AUTHORITY_AND_SOD
    _record_transition(
        session, case, CaseState.REVIEWER_AUTHORITY_AND_SOD, None, identity.identity_id
    )
    context = _authority_context(session, case, identity, rationale=rationale)
    stop = first_mandatory_stop(evaluate_state(context))
    audit.record(
        session,
        event_type=AuditEventType.REVIEWER_AUTHORITY_AND_SOD,
        actor_id=identity.identity_id,
        actor_kind="HUMAN_DEMO_IDENTITY",
        outcome=AuditOutcome.PASS if stop is None else AuditOutcome.DENIED,
        case_id=case.case_id,
        reason_code=stop.reason_code if stop else None,
        severity=Severity.S1_HIGH if stop else None,
    )
    if stop is not None:
        reason = ReasonCode(stop.reason_code)
        _record_transition(
            session, case, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW, reason, identity.identity_id
        )
        raise AccessDeniedError(reason, case_id=case.case_id, safe_to_display=True)

    authority_reverified_at = utc_now()

    # Stage 17 - DISPOSITION_BINDING
    _record_transition(session, case, CaseState.DISPOSITION_BINDING, None, identity.identity_id)
    context = _authority_context(session, case, identity, rationale=rationale)
    stop = first_mandatory_stop(evaluate_state(context))
    if stop is None and expected_packet_sha256 and expected_packet_sha256 != issued_sha256:
        reason = ReasonCode.PACKET_NOT_AVAILABLE
        _record_transition(
            session, case, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW, reason, identity.identity_id
        )
        raise StopError(reason, case_id=case.case_id)
    if stop is not None:
        reason = ReasonCode(stop.reason_code)
        _record_transition(
            session, case, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW, reason, identity.identity_id
        )
        raise StopError(reason, case_id=case.case_id)

    is_final = disposition_value in FINAL_DISPOSITIONS
    if is_final:
        existing = (
            session.execute(
                select(HumanDispositionRow).where(
                    HumanDispositionRow.packet_id == packet_row.packet_id,
                    HumanDispositionRow.packet_version == packet_row.packet_version,
                    HumanDispositionRow.is_final.is_(True),
                )
            )
            .scalars()
            .first()
        )
        if existing is not None:
            reason = ReasonCode.DISPOSITION_ALREADY_FINAL
            _record_transition(
                session,
                case,
                CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW,
                reason,
                identity.identity_id,
            )
            raise StopError(reason, case_id=case.case_id)

    disposition = HumanDisposition(
        produced_by=identity.identity_id,
        disposition_id=derived_id("disposition", case.case_id, disposition_value.value[:12]),
        case_id=case.case_id,
        packet_id=packet_row.packet_id,
        packet_version=packet_row.packet_version,
        packet_sha256=issued_sha256,
        reviewer_identity_id=identity.identity_id,
        reviewer_role_id=identity.role_id,
        disposition_value=disposition_value,
        human_rationale=rationale,
        decided_at=utc_now(),
        authority_reverified_at=authority_reverified_at,
        is_final=is_final,
    )
    session.add(
        HumanDispositionRow(
            disposition_id=disposition.disposition_id,
            case_id=disposition.case_id,
            packet_id=disposition.packet_id,
            packet_version=disposition.packet_version,
            packet_sha256=disposition.packet_sha256,
            reviewer_identity_id=disposition.reviewer_identity_id,
            disposition_value=disposition.disposition_value.value,
            human_rationale=disposition.human_rationale,
            is_final=disposition.is_final,
            decided_at=disposition.decided_at,
            payload=disposition.model_dump(mode="json"),
        )
    )
    session.flush()
    audit.record(
        session,
        event_type=AuditEventType.DISPOSITION_BINDING,
        actor_id=identity.identity_id,
        actor_kind="HUMAN_DEMO_IDENTITY",
        outcome=AuditOutcome.PASS,
        case_id=case.case_id,
        binding=ObjectBinding(
            object_kind="human_disposition",
            object_id=disposition.disposition_id,
            object_version=str(packet_row.packet_version),
            object_sha256=issued_sha256,
        ),
        payload_reference=f"value={disposition_value.value};final={is_final}",
    )

    # Stage 18 - DISPOSITION_CLOSURE_AUDIT (a distinct, later confirmed event)
    _record_transition(
        session, case, CaseState.DISPOSITION_CLOSURE_AUDIT, None, identity.identity_id
    )
    pre_issuance = audit.find_confirmed(session, case.case_id, AuditEventType.PACKET_PRE_ISSUANCE)
    try:
        closure = audit.record_and_confirm(
            session,
            event_type=AuditEventType.DISPOSITION_CLOSURE,
            actor_id=identity.identity_id,
            actor_kind="HUMAN_DEMO_IDENTITY",
            outcome=AuditOutcome.PASS,
            case_id=case.case_id,
            binding=ObjectBinding(
                object_kind="human_disposition",
                object_id=disposition.disposition_id,
                object_version=str(packet_row.packet_version),
                object_sha256=issued_sha256,
            ),
        )
    except RuntimeError as error:
        _record_transition(
            session,
            case,
            CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW,
            ReasonCode.CRITICAL_AUDIT_FAILURE,
            identity.identity_id,
        )
        raise StopError(ReasonCode.CRITICAL_AUDIT_FAILURE, case_id=case.case_id) from error

    context = _authority_context(session, case, identity, rationale=rationale)
    context.confirmed_pre_issuance_event_id = pre_issuance.event_id if pre_issuance else None
    context.confirmed_closure_event_id = closure.event_id
    stop = first_mandatory_stop(evaluate_state(context))
    if stop is not None:
        _record_transition(
            session,
            case,
            CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW,
            ReasonCode(stop.reason_code),
            identity.identity_id,
        )
        raise StopError(ReasonCode(stop.reason_code), case_id=case.case_id)

    sealed = with_audit_binding(
        packet.model_copy(update={"disposition": disposition if is_final else None}),
        closure_event_id=closure.event_id,
        closure_confirmed_at=closure.application_time,
    )
    failures = validate_packet_semantics(
        sealed,
        SemanticContext(
            case_id=case.case_id,
            authorization=primary_authorization(),
            eligible_source_keys=frozenset(
                f"{item.source_id}@{item.source_version}" for item in packet.evidence_manifest
            ),
            admitted_excerpt_ids=frozenset(item.excerpt_id for item in packet.evidence_manifest),
            issued_packet_sha256=issued_sha256,
            confirmed_pre_issuance_event_id=pre_issuance.event_id if pre_issuance else None,
            confirmed_pre_issuance_at=pre_issuance.application_time if pre_issuance else None,
            confirmed_closure_event_id=closure.event_id,
            confirmed_closure_at=closure.application_time,
        ),
    )
    if failures:
        _record_transition(
            session,
            case,
            CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW,
            ReasonCode.PACKET_CONTRACT_FAILURE,
            identity.identity_id,
        )
        raise StopError(ReasonCode.PACKET_CONTRACT_FAILURE, case_id=case.case_id)

    row = session.get(HumanDispositionRow, disposition.disposition_id)
    if row is not None:
        row.closure_event_id = closure.event_id

    # Stage 19 - CLOSED_DECISION_SUPPORT_RECORD, or back to waiting for a clarification.
    if is_final:
        _record_transition(
            session, case, CaseState.CLOSED_DECISION_SUPPORT_RECORD, None, identity.identity_id
        )
        terminal = CaseState.CLOSED_DECISION_SUPPORT_RECORD
    else:
        _record_transition(
            session, case, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW, None, identity.identity_id
        )
        terminal = CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW

    packet_row.payload = sealed.model_dump(mode="json")
    # issued_sha256 is deliberately left untouched: it is what the audit event bound and
    # what the reviewer disposed of.
    packet_row.packet_sha256 = sealed.integrity.packet_sha256
    from app.domain.canonical import canonical_dumps

    packet_row.canonical_json = canonical_dumps(packet_row.payload)
    case.route = Route.HUMAN_REVIEW_REQUIRED.value
    session.flush()

    return DispositionOutcome(
        case_id=case.case_id,
        disposition=disposition,
        packet=sealed,
        terminal_state=terminal,
        closure_event_id=closure.event_id,
        is_final=is_final,
    )


def guard_no_execution(disposition_value: DispositionValue) -> None:
    """Explicit terminal non-execution guard.

    There is no connector to call, so this function exists to make the boundary visible and
    testable rather than implicit: if a future change ever adds a downstream effect here,
    the prohibited-path tests fail.
    """
    if disposition_value not in set(DispositionValue):
        raise ControlError(ReasonCode.PROHIBITED_ACTION_PATH_DETECTED)
