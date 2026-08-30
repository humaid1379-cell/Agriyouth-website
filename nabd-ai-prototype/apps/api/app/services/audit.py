"""Append-only audit chain.

Each case owns a hash chain. Event ``n`` binds the hash of event ``n-1``, so a removed,
reordered or edited event is detectable by recomputation. The chain hash is tamper
evidence: it proves the log is internally consistent, not that the log is complete or that
the facts in it are true.

Critical events (packet pre-issuance and disposition closure) are *confirmed*, which here
means durably committed and then re-read. If confirmation cannot be persisted, the caller
rolls back and the case fails closed rather than displaying a packet or closing a record.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.canonical import utc_now
from app.domain.enums import AuditEventType, AuditOutcome, CaseState, Severity
from app.domain.ids import new_id
from app.domain.versions import AUDIT_CHAIN_VERSION
from app.repositories.tables import AuditEventRow
from app.schemas.audit import GENESIS_PREVIOUS_HASH, AuditChainVerification, AuditEvent, ObjectBinding

AUDIT_SERVICE_ID = "service:audit-chain"
GLOBAL_CHAIN_KEY = "GLOBAL"


def chain_key_for(case_id: str | None) -> str:
    return case_id or GLOBAL_CHAIN_KEY


def _next_sequence(session: Session, chain_key: str) -> int:
    current = session.execute(
        select(func.max(AuditEventRow.sequence)).where(AuditEventRow.chain_key == chain_key)
    ).scalar()
    return int(current or 0) + 1


def _previous_hash(session: Session, chain_key: str, sequence: int) -> str:
    if sequence <= 1:
        return GENESIS_PREVIOUS_HASH
    previous = session.execute(
        select(AuditEventRow.event_hash)
        .where(AuditEventRow.chain_key == chain_key, AuditEventRow.sequence == sequence - 1)
    ).scalar()
    return str(previous) if previous else GENESIS_PREVIOUS_HASH


def build_event(
    session: Session,
    *,
    event_type: AuditEventType,
    actor_id: str,
    outcome: AuditOutcome,
    case_id: str | None = None,
    actor_kind: str = "SERVICE",
    binding: ObjectBinding | None = None,
    from_state: CaseState | None = None,
    to_state: CaseState | None = None,
    reason_code: str | None = None,
    severity: Severity | None = None,
    payload_reference: str = "",
    application_time: datetime | None = None,
    event_id: str | None = None,
) -> AuditEvent:
    """Build a chained event.

    ``event_id`` may be supplied when a governed object must reference the event before the
    event exists. The packet does exactly that: it carries its pre-issuance event id inside
    the sealed preimage, so the id is generated first and the event is written afterwards
    binding the resulting hash. Without this the two would chase each other.
    """
    key = chain_key_for(case_id)
    sequence = _next_sequence(session, key)
    event = AuditEvent(
        produced_by=AUDIT_SERVICE_ID,
        event_id=event_id or new_id("event"),
        event_type=event_type,
        case_id=case_id,
        sequence=sequence,
        application_time=application_time or utc_now(),
        actor_id=actor_id,
        actor_kind="HUMAN_DEMO_IDENTITY" if actor_kind == "HUMAN_DEMO_IDENTITY" else "SERVICE",
        binding=binding,
        from_state=from_state,
        to_state=to_state,
        outcome=outcome,
        reason_code=reason_code,
        severity=severity,
        payload_reference=payload_reference,
        previous_event_hash=_previous_hash(session, key, sequence),
        confirmed=True,
    )
    return event.with_hash()


def persist_event(session: Session, event: AuditEvent) -> AuditEventRow:
    row = AuditEventRow(
        event_id=event.event_id,
        chain_key=chain_key_for(event.case_id),
        sequence=event.sequence,
        event_type=event.event_type.value,
        case_id=event.case_id,
        application_time=event.application_time,
        actor_id=event.actor_id,
        actor_kind=event.actor_kind,
        outcome=event.outcome.value,
        reason_code=event.reason_code,
        severity=event.severity.value if event.severity else None,
        from_state=event.from_state.value if event.from_state else None,
        to_state=event.to_state.value if event.to_state else None,
        previous_event_hash=event.previous_event_hash,
        event_hash=event.event_hash,
        confirmed=event.confirmed,
        payload=event.model_dump(mode="json"),
        created_at=event.created_at,
    )
    session.add(row)
    session.flush()
    return row


def record(
    session: Session,
    *,
    event_type: AuditEventType,
    actor_id: str,
    outcome: AuditOutcome,
    **kwargs: object,
) -> AuditEvent:
    """Append one event to its chain."""
    event = build_event(
        session, event_type=event_type, actor_id=actor_id, outcome=outcome, **kwargs  # type: ignore[arg-type]
    )
    persist_event(session, event)
    return event


def record_and_confirm(
    session: Session,
    *,
    event_type: AuditEventType,
    actor_id: str,
    outcome: AuditOutcome,
    **kwargs: object,
) -> AuditEvent:
    """Append a critical event, commit it, then re-read it to confirm durability.

    Returning normally means the event is durable. Raising means the caller must fail
    closed: no packet display, no disposition closure.
    """
    event = record(session, event_type=event_type, actor_id=actor_id, outcome=outcome, **kwargs)
    session.commit()
    stored = session.get(AuditEventRow, event.event_id)
    if stored is None or stored.event_hash != event.event_hash or not stored.confirmed:
        raise RuntimeError("critical audit event could not be confirmed after commit")
    return event


def load_chain(session: Session, case_id: str | None) -> list[AuditEventRow]:
    key = chain_key_for(case_id)
    return list(
        session.execute(
            select(AuditEventRow)
            .where(AuditEventRow.chain_key == key)
            .order_by(AuditEventRow.sequence.asc())
        ).scalars()
    )


def verify_chain(session: Session, case_id: str | None) -> AuditChainVerification:
    """Recompute every event hash and report the first divergence."""
    rows = load_chain(session, case_id)
    checked_at = utc_now()
    if not rows:
        return AuditChainVerification(
            case_id=case_id,
            chain_version=AUDIT_CHAIN_VERSION,
            event_count=0,
            verified=True,
            checked_at=checked_at,
        )

    expected_previous = GENESIS_PREVIOUS_HASH
    expected_sequence = 1
    for row in rows:
        divergence: str | None = None
        if row.sequence != expected_sequence:
            divergence = "SEQUENCE_GAP_OR_REORDER"
        elif row.previous_event_hash != expected_previous:
            divergence = "PREVIOUS_HASH_MISMATCH"
        else:
            event = AuditEvent.model_validate(row.payload)
            if event.event_hash != row.event_hash:
                divergence = "STORED_HASH_DIFFERS_FROM_PAYLOAD"
            elif not event.hash_matches():
                divergence = "EVENT_HASH_MISMATCH"

        if divergence:
            return AuditChainVerification(
                case_id=case_id,
                chain_version=AUDIT_CHAIN_VERSION,
                event_count=len(rows),
                verified=False,
                first_divergence_sequence=row.sequence,
                first_divergence_event_id=row.event_id,
                first_divergence_kind=divergence,
                head_hash=rows[-1].event_hash,
                checked_at=checked_at,
            )
        expected_previous = row.event_hash
        expected_sequence += 1

    return AuditChainVerification(
        case_id=case_id,
        chain_version=AUDIT_CHAIN_VERSION,
        event_count=len(rows),
        verified=True,
        head_hash=rows[-1].event_hash,
        checked_at=checked_at,
    )


def find_confirmed(
    session: Session, case_id: str, event_type: AuditEventType
) -> AuditEventRow | None:
    return session.execute(
        select(AuditEventRow)
        .where(
            AuditEventRow.case_id == case_id,
            AuditEventRow.event_type == event_type.value,
            AuditEventRow.confirmed.is_(True),
            AuditEventRow.outcome == AuditOutcome.PASS.value,
        )
        .order_by(AuditEventRow.sequence.desc())
    ).scalars().first()
