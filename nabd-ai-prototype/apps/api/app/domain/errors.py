"""Typed control failures.

Every failure surfaced by the API is one of these. The HTTP layer renders them into the
single error envelope defined in the API contract and never adds free-form detail.
"""

from __future__ import annotations

from app.domain.enums import CaseState, Severity
from app.domain.reason_codes import ReasonCode, message_for


class ControlError(Exception):
    """A deterministic, reason-coded failure. Never carries secrets or case content."""

    http_status: int = 422

    def __init__(
        self,
        code: ReasonCode,
        *,
        case_id: str | None = None,
        state: CaseState | None = None,
        safe_to_display: bool = True,
        severity: Severity | None = None,
        message: str | None = None,
    ) -> None:
        self.code = code
        self.case_id = case_id
        self.state = state
        self.safe_to_display = safe_to_display
        self.severity = severity
        self.message = message or message_for(code)
        super().__init__(self.message)

    def envelope(self, correlation_id: str) -> dict[str, object]:
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "case_id": self.case_id,
                "state": self.state.value if self.state else None,
                "correlation_id": correlation_id,
                "safe_to_display": self.safe_to_display,
            }
        }


class AuthorizationError(ControlError):
    """Authorization fixture missing, expired or out of scope."""

    http_status = 403


class IdentityError(ControlError):
    """Session, role or scope could not be verified. Discloses no case content."""

    http_status = 401


class AccessDeniedError(ControlError):
    """Identity is known but not permitted. Discloses no case content."""

    http_status = 403


class NotFoundError(ControlError):
    """Object absent, or present but invisible to this identity. Identical either way."""

    http_status = 404


class LimitExceededError(ControlError):
    http_status = 429


class StopError(ControlError):
    """A mandatory stop that routes the case to ``CANNOT_PROCEED``."""

    http_status = 422


class SecurityError(ControlError):
    """A prohibited path was attempted. Always recorded as a security audit event."""

    http_status = 403

    def __init__(
        self,
        code: ReasonCode = ReasonCode.PROHIBITED_ACTION_PATH_DETECTED,
        *,
        case_id: str | None = None,
        state: CaseState | None = None,
        severity: Severity = Severity.S0_CRITICAL,
        message: str | None = None,
    ) -> None:
        super().__init__(
            code,
            case_id=case_id,
            state=state,
            safe_to_display=True,
            severity=severity,
            message=message,
        )


class IllegalTransitionError(ControlError):
    """An FSM edge that is not declared. Always logged as a critical event."""

    http_status = 409

    def __init__(
        self,
        *,
        case_id: str | None = None,
        from_state: CaseState | None = None,
        to_state: CaseState | None = None,
    ) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            ReasonCode.ILLEGAL_STATE_TRANSITION,
            case_id=case_id,
            state=from_state,
            severity=Severity.S0_CRITICAL,
        )
