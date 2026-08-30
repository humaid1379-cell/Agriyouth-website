"""Server-controlled demo sessions.

The browser may select a demo profile by identity id. It never submits a role, a scope, an
authority level or a separation-of-duties fact. The API issues a short-lived HMAC-signed
token, stores only its SHA-256, and derives every trusted field from the seeded fixture on
each request.

This is a synthetic session mechanism for an isolated prototype. It is deliberately not an
OAuth client, not an identity-provider integration and not a password system.
"""

from __future__ import annotations

import hmac
import secrets
from datetime import timedelta
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.canonical import utc_now
from app.domain.enums import IdentityStatus
from app.domain.errors import IdentityError
from app.domain.ids import derived_id, new_id
from app.domain.reason_codes import ReasonCode
from app.repositories.tables import DemoSessionRow
from app.schemas.governance import DemoIdentity, IdentityAssertion
from app.services.fixtures import load_identities

IDENTITY_SERVICE_ID = "service:demo-identity"
TOKEN_SEPARATOR = "."


def _sign(session_id: str, nonce: str) -> str:
    settings = get_settings()
    message = f"{session_id}{TOKEN_SEPARATOR}{nonce}".encode()
    return hmac.new(settings.demo_session_secret.encode(), message, sha256).hexdigest()


def token_digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def selectable_identities() -> list[DemoIdentity]:
    return [identity for identity in load_identities().values() if identity.selectable_in_ui]


def create_session(db: Session, identity_id: str) -> tuple[str, IdentityAssertion]:
    """Issue a demo session for a seeded, selectable, active identity."""
    identities = load_identities()
    identity = identities.get(identity_id)
    if identity is None or not identity.selectable_in_ui:
        # An unknown identity and a non-selectable identity are indistinguishable to the
        # caller, so probing tells an attacker nothing.
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)
    if identity.status is not IdentityStatus.ACTIVE:
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)

    settings = get_settings()
    issued_at = utc_now()
    expires_at = issued_at + timedelta(seconds=settings.demo_session_ttl_seconds)
    session_id = new_id("session")
    nonce = secrets.token_urlsafe(16)
    token = f"{session_id}{TOKEN_SEPARATOR}{nonce}{TOKEN_SEPARATOR}{_sign(session_id, nonce)}"

    db.add(
        DemoSessionRow(
            session_id=session_id,
            identity_id=identity.identity_id,
            issued_at=issued_at,
            expires_at=expires_at,
            revoked=False,
            token_sha256=token_digest(token),
        )
    )
    db.flush()
    return token, _assertion(identity, session_id, issued_at, expires_at)


def _assertion(
    identity: DemoIdentity, session_id: str, issued_at, expires_at  # type: ignore[no-untyped-def]
) -> IdentityAssertion:
    return IdentityAssertion(
        produced_by=IDENTITY_SERVICE_ID,
        assertion_id=derived_id("assertion", session_id, "a1"),
        session_id=session_id,
        identity_id=identity.identity_id,
        role=identity.role,
        role_id=identity.role_id,
        business_scope_id=identity.business_scope_id,
        status=identity.status,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def resolve_session(db: Session, token: str) -> IdentityAssertion:
    """Derive the trusted identity for a token, or deny without disclosing why."""
    parts = token.split(TOKEN_SEPARATOR)
    if len(parts) != 3:
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)
    session_id, nonce, signature = parts
    if not hmac.compare_digest(signature, _sign(session_id, nonce)):
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)

    row = db.execute(
        select(DemoSessionRow).where(DemoSessionRow.session_id == session_id)
    ).scalars().first()
    if row is None or row.revoked:
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)
    if not hmac.compare_digest(row.token_sha256, token_digest(token)):
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)

    now = utc_now()
    if now >= row.expires_at:
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)

    identity = load_identities().get(row.identity_id)
    if identity is None or identity.status is not IdentityStatus.ACTIVE:
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)

    return _assertion(identity, session_id, row.issued_at, row.expires_at)


def revoke_session(db: Session, session_id: str) -> None:
    row = db.get(DemoSessionRow, session_id)
    if row is not None:
        row.revoked = True
        db.flush()


def assertion_for_fixture(identity_id: str, *, minutes: int = 60) -> IdentityAssertion:
    """Build an assertion directly from a fixture, for tests and the TEVV harness.

    This bypasses the HTTP session issuance path on purpose: denial fixtures such as the
    expired and revoked identities are not issuable through :func:`create_session`.
    """
    identity = load_identities()[identity_id]
    issued_at = utc_now()
    return _assertion(
        identity, derived_id("session", identity_id, "fixture"), issued_at,
        issued_at + timedelta(minutes=minutes),
    )
