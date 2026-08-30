"""Request-scoped dependencies.

Identity is always derived server-side from the demo session token. No route reads a role,
scope or authority field from the request body, query string or a header other than the
bearer token itself.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.domain.enums import DemoRole
from app.domain.errors import AccessDeniedError, IdentityError, NotFoundError
from app.domain.reason_codes import ReasonCode
from app.repositories.database import get_db
from app.repositories.tables import CaseRow
from app.schemas.governance import IdentityAssertion
from app.services.identity import resolve_session


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


DbSession = Annotated[Session, Depends(db_session)]


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def current_identity(
    db: DbSession,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> IdentityAssertion:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise IdentityError(ReasonCode.REQUESTER_OR_SESSION_INVALID)
    return resolve_session(db, authorization.split(" ", 1)[1].strip())


CurrentIdentity = Annotated[IdentityAssertion, Depends(current_identity)]


def require_role(*roles: DemoRole):  # type: ignore[no-untyped-def]
    def dependency(identity: CurrentIdentity) -> IdentityAssertion:
        if identity.role not in roles:
            raise AccessDeniedError(ReasonCode.ACCESS_DENIED)
        return identity

    return dependency


RequesterIdentity = Annotated[IdentityAssertion, Depends(require_role(DemoRole.REQUESTER))]
ReviewerIdentity = Annotated[IdentityAssertion, Depends(require_role(DemoRole.REVIEWER))]
AdminIdentity = Annotated[IdentityAssertion, Depends(require_role(DemoRole.ADMINISTRATOR))]


def load_visible_case(db: Session, case_id: str, identity: IdentityAssertion) -> CaseRow:
    """Fetch a case scoped to the identity.

    An invisible case and an absent case return the identical ``NOT_FOUND``, so probing a
    case id reveals nothing about whether it exists.
    """
    case = db.get(CaseRow, case_id)
    if case is None:
        raise NotFoundError(ReasonCode.NOT_FOUND)
    if case.business_scope_id != identity.business_scope_id:
        raise NotFoundError(ReasonCode.NOT_FOUND)
    if identity.role is DemoRole.REQUESTER and case.requester_identity_id != identity.identity_id:
        raise NotFoundError(ReasonCode.NOT_FOUND)
    if identity.role is DemoRole.ADMINISTRATOR:
        # The administrator operates controls and never reads case content.
        raise AccessDeniedError(ReasonCode.ACCESS_DENIED)
    return case
