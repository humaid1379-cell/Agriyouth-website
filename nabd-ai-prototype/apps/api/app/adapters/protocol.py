"""Model adapter protocol and fault-mode vocabulary.

An adapter is a thin transport that returns **raw text**. The gateway owns the call budget,
the timeout, the size limit, the prohibited-marker scan, the JSON parse and the closed
schema validation. Keeping adapters raw means the schema enforcement is real rather than
implied by the return type.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.domain.enums import Severity
from app.domain.errors import ControlError
from app.domain.reason_codes import ReasonCode
from app.schemas.model_io import DraftRequest, VerificationRequest


class ModelFault(StrEnum):
    """Fault modes the deterministic mock can be asked to produce, for tests only.

    The fault profile is a service-layer argument set by the TEVV harness. It is not an
    API field, not a request-body field and not reachable from the browser.
    """

    NONE = "NONE"
    DRAFT_TIMEOUT = "DRAFT_TIMEOUT"
    VERIFIER_TIMEOUT = "VERIFIER_TIMEOUT"
    DRAFT_MALFORMED = "DRAFT_MALFORMED"
    VERIFIER_MALFORMED = "VERIFIER_MALFORMED"
    DRAFT_REFUSAL = "DRAFT_REFUSAL"
    VERIFIER_DISAGREEMENT = "VERIFIER_DISAGREEMENT"
    FABRICATED_CITATION = "FABRICATED_CITATION"
    PARTIAL_SUPPORT = "PARTIAL_SUPPORT"
    OVERSIZED_OUTPUT = "OVERSIZED_OUTPUT"
    THIRD_CALL_ATTEMPT = "THIRD_CALL_ATTEMPT"
    TOOL_REQUEST = "TOOL_REQUEST"
    FALLBACK_ATTEMPT = "FALLBACK_ATTEMPT"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class RawModelResponse:
    """Untyped transport result. Nothing downstream trusts it until it is validated."""

    text: str
    duration_ms: int
    model_revision: str


class ModelAdapterError(ControlError):
    """A typed adapter failure. It never carries a prompt, a credential or raw output."""

    http_status = 502

    def __init__(
        self,
        code: ReasonCode,
        *,
        raw_output_chars: int = 0,
        severity: Severity | None = None,
        detail: str = "",
    ) -> None:
        self.raw_output_chars = raw_output_chars
        self.detail = detail
        super().__init__(code, safe_to_display=True, severity=severity)


@runtime_checkable
class ModelAdapter(Protocol):
    """The only interface the orchestrator knows about."""

    name: str
    supports_tool_calling: bool
    supports_fallback: bool

    def draft(self, request: DraftRequest) -> RawModelResponse: ...

    def verify(self, request: VerificationRequest) -> RawModelResponse: ...
