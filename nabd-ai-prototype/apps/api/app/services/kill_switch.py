"""Administrator emergency stop.

State is derived from the append-only ``kill_switch_events`` log rather than a mutable
flag, so every toggle keeps its actor, reason and timestamp. While the switch is active,
``KILL-001`` stops intake, processing and disposition at the highest rule precedence.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.canonical import utc_now
from app.domain.enums import AuditEventType, AuditOutcome, Severity
from app.domain.ids import new_id
from app.repositories.tables import KillSwitchEventRow
from app.schemas.governance import KillSwitchState
from app.services import audit


def latest_event(session: Session) -> KillSwitchEventRow | None:
    return session.execute(
        select(KillSwitchEventRow).order_by(KillSwitchEventRow.occurred_at.desc())
    ).scalars().first()


def kill_switch_active(session: Session) -> bool:
    event = latest_event(session)
    return bool(event and event.active)


def current_state(session: Session) -> KillSwitchState:
    event = latest_event(session)
    if event is None:
        return KillSwitchState(active=False)
    return KillSwitchState(
        active=event.active,
        changed_at=event.occurred_at,
        changed_by=event.actor_id,
        reason=event.reason,
    )


def set_kill_switch(session: Session, *, active: bool, actor_id: str, reason: str) -> KillSwitchState:
    occurred_at = utc_now()
    session.add(
        KillSwitchEventRow(
            kill_switch_event_id=new_id("kill_switch"),
            active=active,
            actor_id=actor_id,
            reason=reason,
            occurred_at=occurred_at,
        )
    )
    audit.record(
        session,
        event_type=AuditEventType.KILL_SWITCH,
        actor_id=actor_id,
        actor_kind="HUMAN_DEMO_IDENTITY",
        outcome=AuditOutcome.RECORDED,
        severity=Severity.S1_HIGH if active else None,
        payload_reference=f"active={active}",
    )
    session.flush()
    return KillSwitchState(active=active, changed_at=occurred_at, changed_by=actor_id, reason=reason)
