"""Append-only audit event contract and chain arithmetic.

Chain rule: ``event_hash = SHA256(canonical_json(event_body_without_event_hash))`` where the
body contains ``previous_event_hash``. The genesis event of a case chains from 64 zeros.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import Field

from app.domain.canonical import canonical_sha256
from app.domain.enums import AuditEventType, AuditOutcome, CaseState, Severity
from app.schemas.base import HashStr, IdStr, StrictModel, VersionedRecord, VersionStr

GENESIS_PREVIOUS_HASH: str = "0" * 64


class ObjectBinding(StrictModel):
    """Binds an event to the exact object version and hash it concerns."""

    object_kind: str
    object_id: IdStr
    object_version: VersionStr | None = None
    object_sha256: HashStr | None = None


class AuditEvent(VersionedRecord):
    event_id: IdStr
    event_type: AuditEventType
    case_id: IdStr | None = None
    sequence: Annotated[int, Field(ge=1)]
    application_time: datetime
    actor_id: IdStr
    actor_kind: Literal["HUMAN_DEMO_IDENTITY", "SERVICE"] = "SERVICE"
    binding: ObjectBinding | None = None
    from_state: CaseState | None = None
    to_state: CaseState | None = None
    outcome: AuditOutcome
    reason_code: str | None = None
    severity: Severity | None = None
    payload_reference: str = Field(
        default="",
        description="Minimum necessary reference. Never full case content or model prompts.",
    )
    previous_event_hash: HashStr = GENESIS_PREVIOUS_HASH
    event_hash: HashStr = "0" * 64
    confirmed: bool = False

    def hash_preimage(self) -> dict[str, Any]:
        body = self.model_dump(mode="json")
        body.pop("event_hash", None)
        return body

    def compute_hash(self) -> str:
        return canonical_sha256(self.hash_preimage())

    def with_hash(self) -> AuditEvent:
        return self.model_copy(update={"event_hash": self.compute_hash()})

    def hash_matches(self) -> bool:
        return self.event_hash == self.compute_hash()


class AuditChainVerification(StrictModel):
    case_id: IdStr | None
    chain_version: VersionStr
    event_count: int
    verified: bool
    first_divergence_sequence: int | None = None
    first_divergence_event_id: IdStr | None = None
    first_divergence_kind: str | None = None
    head_hash: HashStr | None = None
    checked_at: datetime


class KillSwitchEvent(VersionedRecord):
    kill_switch_event_id: IdStr
    active: bool
    actor_id: IdStr
    reason: str
    occurred_at: datetime
