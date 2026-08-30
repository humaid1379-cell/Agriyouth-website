"""The model gateway.

Everything that makes a model call safe lives here, not in the adapter and not in a prompt:

* a hard two-call budget per case (one draft, one verifier);
* at most one same-endpoint retry, and only when no partial result was accepted;
* a per-call timeout and an output character limit;
* a prohibited-marker scan for tool requests, URLs and action verbs;
* a closed-schema parse that never coerces an invalid answer into valid JSON.

A malformed, refused, timed-out, over-limit, unavailable, wrong-version, wrong-schema or
attempted-fallback response produces a reason-coded failure.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import ValidationError

from app.adapters.protocol import ModelAdapter, ModelAdapterError, RawModelResponse
from app.domain.canonical import text_sha256, utc_now
from app.domain.enums import ModelMode, ModelTaskRole, Severity
from app.domain.ids import derived_id
from app.domain.limits import (
    DRAFT_CALLS_MAX,
    MODEL_CALLS_MAX,
    MODEL_OUTPUT_MAX_CHARS,
    SAME_ENDPOINT_RETRY_MAX,
    VERIFIER_CALLS_MAX,
)
from app.domain.reason_codes import ReasonCode
from app.schemas.model_io import (
    PROHIBITED_OUTPUT_MARKERS,
    DraftRequest,
    DraftResponse,
    ModelConfiguration,
    ModelRunRecord,
    VerificationRequest,
    VerificationResponse,
)

GATEWAY_SERVICE_ID = "service:model-gateway"


class ModelBudgetExceeded(ModelAdapterError):
    """Raised when a third model call, or a second call of one role, is attempted."""


@dataclass(slots=True)
class CallBudget:
    """Per-case model call accounting. There is exactly one of these per case."""

    draft_calls: int = 0
    verifier_calls: int = 0
    retries: int = 0
    partial_result_accepted: bool = False

    @property
    def total_calls(self) -> int:
        return self.draft_calls + self.verifier_calls

    def reserve(self, task_role: ModelTaskRole) -> None:
        if self.total_calls >= MODEL_CALLS_MAX:
            raise ModelBudgetExceeded(
                ReasonCode.MODEL_CALL_LIMIT_EXCEEDED,
                severity=Severity.S1_HIGH,
                detail="the two-call budget for this case is exhausted",
            )
        if task_role is ModelTaskRole.DRAFTER:
            if self.draft_calls >= DRAFT_CALLS_MAX:
                raise ModelBudgetExceeded(
                    ReasonCode.MODEL_CALL_LIMIT_EXCEEDED, detail="draft budget exhausted"
                )
            self.draft_calls += 1
        else:
            if self.verifier_calls >= VERIFIER_CALLS_MAX:
                raise ModelBudgetExceeded(
                    ReasonCode.MODEL_CALL_LIMIT_EXCEEDED, detail="verifier budget exhausted"
                )
            self.verifier_calls += 1

    def reserve_retry(self) -> None:
        if self.partial_result_accepted:
            raise ModelAdapterError(
                ReasonCode.RETRY_LIMIT_EXCEEDED,
                detail="a partial result was accepted, so no retry is permitted",
            )
        if self.retries >= SAME_ENDPOINT_RETRY_MAX:
            raise ModelAdapterError(
                ReasonCode.RETRY_LIMIT_EXCEEDED, detail="same-endpoint retry budget exhausted"
            )
        self.retries += 1


@dataclass(slots=True)
class GatewayOutcome:
    run: ModelRunRecord
    draft: DraftResponse | None = None
    verification: VerificationResponse | None = None


@dataclass(slots=True)
class ModelGateway:
    adapter: ModelAdapter
    draft_configuration: ModelConfiguration
    verify_configuration: ModelConfiguration
    mode: ModelMode
    budget: CallBudget = field(default_factory=CallBudget)
    runs: list[ModelRunRecord] = field(default_factory=list)

    # -- shared plumbing ---------------------------------------------------------
    def _configuration(self, task_role: ModelTaskRole) -> ModelConfiguration:
        return (
            self.draft_configuration
            if task_role is ModelTaskRole.DRAFTER
            else self.verify_configuration
        )

    def _assert_adapter_boundaries(self) -> None:
        if getattr(self.adapter, "supports_tool_calling", False):
            raise ModelAdapterError(
                ReasonCode.MODEL_CONFIGURATION_MISMATCH,
                severity=Severity.S0_CRITICAL,
                detail="adapter advertises tool calling, which V1 forbids",
            )
        if getattr(self.adapter, "supports_fallback", False):
            raise ModelAdapterError(
                ReasonCode.MODEL_FALLBACK_ATTEMPTED,
                severity=Severity.S0_CRITICAL,
                detail="adapter advertises fallback, which V1 forbids",
            )

    def _validate_configuration(self, configuration: ModelConfiguration) -> None:
        if configuration.revoked or not configuration.is_current(utc_now()):
            raise ModelAdapterError(
                ReasonCode.MODEL_CONFIGURATION_MISMATCH,
                detail="the pinned model configuration is revoked or out of its period",
            )
        if configuration.tool_calling_enabled or configuration.fallback_enabled:
            raise ModelAdapterError(
                ReasonCode.MODEL_CONFIGURATION_MISMATCH,
                severity=Severity.S0_CRITICAL,
                detail="configuration enables tools or fallback, which V1 forbids",
            )

    def _screen_output(self, raw: RawModelResponse, configuration: ModelConfiguration) -> None:
        limit = min(configuration.output_limit_chars, MODEL_OUTPUT_MAX_CHARS)
        if len(raw.text) > limit:
            raise ModelAdapterError(
                ReasonCode.MODEL_OUTPUT_LIMIT_EXCEEDED, raw_output_chars=len(raw.text)
            )
        if raw.model_revision != configuration.model_revision:
            raise ModelAdapterError(
                ReasonCode.MODEL_CONFIGURATION_MISMATCH,
                severity=Severity.S0_CRITICAL,
                detail="the response came from a model revision other than the pinned one",
            )
        lowered = raw.text.casefold()
        for marker in PROHIBITED_OUTPUT_MARKERS:
            if marker.casefold() in lowered:
                raise ModelAdapterError(
                    ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                    severity=Severity.S0_CRITICAL,
                    raw_output_chars=len(raw.text),
                    detail=f"prohibited marker in model output: {marker}",
                )

    @staticmethod
    def _parse(raw_text: str) -> dict[str, object]:
        import json

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ModelAdapterError(
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                raw_output_chars=len(raw_text),
                detail="response is not valid JSON",
            ) from exc
        if not isinstance(parsed, dict):
            raise ModelAdapterError(
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                raw_output_chars=len(raw_text),
                detail="response is not a JSON object",
            )
        if "refusal" in parsed:
            raise ModelAdapterError(ReasonCode.MODEL_REFUSAL, raw_output_chars=len(raw_text))
        return parsed

    def _parse_recording(
        self,
        raw: RawModelResponse,
        task_role: ModelTaskRole,
        configuration: ModelConfiguration,
        case_id: str,
        rendered_input: str,
    ) -> dict[str, object]:
        """Parse, recording the attempt as a failed model run if it does not parse."""
        try:
            return self._parse(raw.text)
        except ModelAdapterError as error:
            self._record_run(
                case_id=case_id,
                task_role=task_role,
                configuration=configuration,
                rendered_input=rendered_input,
                raw_text=raw.text,
                duration_ms=raw.duration_ms,
                succeeded=False,
                reason_code=error.code.value,
            )
            raise

    def _record_run(
        self,
        *,
        case_id: str,
        task_role: ModelTaskRole,
        configuration: ModelConfiguration,
        rendered_input: str,
        raw_text: str,
        duration_ms: int,
        succeeded: bool,
        reason_code: str | None,
    ) -> ModelRunRecord:
        call_index = self.budget.draft_calls if task_role is ModelTaskRole.DRAFTER else 2
        record = ModelRunRecord(
            produced_by=GATEWAY_SERVICE_ID,
            model_run_id=derived_id("model_run", case_id, task_role.value.lower()),
            case_id=case_id,
            model_configuration_id=configuration.model_configuration_id,
            task_role=task_role,
            call_index=max(1, min(call_index, 2)),
            retry_count=self.budget.retries,
            input_chars=len(rendered_input),
            output_chars=len(raw_text),
            input_sha256=text_sha256(rendered_input),
            output_sha256=text_sha256(raw_text),
            duration_ms=duration_ms,
            succeeded=succeeded,
            reason_code=reason_code,
            mode=self.mode,
        )
        self.runs.append(record)
        return record

    def _invoke(
        self,
        *,
        task_role: ModelTaskRole,
        case_id: str,
        rendered_input: str,
        call: Callable[[], RawModelResponse],
    ) -> RawModelResponse:
        """Reserve budget, call once, and allow at most one same-endpoint retry."""
        self._assert_adapter_boundaries()
        configuration = self._configuration(task_role)
        self._validate_configuration(configuration)
        self.budget.reserve(task_role)

        attempt = 0
        while True:
            try:
                raw = call()
                self._screen_output(raw, configuration)
                return raw
            except ModelAdapterError as error:
                retryable = error.code in {ReasonCode.MODEL_TIMEOUT, ReasonCode.MODEL_UNAVAILABLE}
                if retryable and attempt == 0 and self.budget.retries < SAME_ENDPOINT_RETRY_MAX:
                    try:
                        self.budget.reserve_retry()
                    except ModelAdapterError:
                        self._record_run(
                            case_id=case_id,
                            task_role=task_role,
                            configuration=configuration,
                            rendered_input=rendered_input,
                            raw_text="",
                            duration_ms=0,
                            succeeded=False,
                            reason_code=error.code.value,
                        )
                        raise
                    attempt += 1
                    continue
                self._record_run(
                    case_id=case_id,
                    task_role=task_role,
                    configuration=configuration,
                    rendered_input=rendered_input,
                    raw_text="",
                    duration_ms=0,
                    succeeded=False,
                    reason_code=error.code.value,
                )
                raise

    # -- public surface ----------------------------------------------------------
    def draft(self, request: DraftRequest) -> GatewayOutcome:
        raw = self._invoke(
            task_role=ModelTaskRole.DRAFTER,
            case_id=request.case_id,
            rendered_input=request.rendered_input,
            call=lambda: self.adapter.draft(request),
        )
        configuration = self.draft_configuration
        parsed = self._parse_recording(
            raw, ModelTaskRole.DRAFTER, configuration, request.case_id, request.rendered_input
        )
        try:
            response = DraftResponse.model_validate(parsed)
        except ValidationError as exc:
            self._record_run(
                case_id=request.case_id,
                task_role=ModelTaskRole.DRAFTER,
                configuration=configuration,
                rendered_input=request.rendered_input,
                raw_text=raw.text,
                duration_ms=raw.duration_ms,
                succeeded=False,
                reason_code=ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE.value,
            )
            raise ModelAdapterError(
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                raw_output_chars=len(raw.text),
                detail="draft response failed closed-schema validation",
            ) from exc

        admitted = request.admitted_excerpt_ids
        unknown = sorted(
            {
                evidence_id
                for claim in response.claims
                for evidence_id in claim.proposed_evidence_ids
                if evidence_id not in admitted
            }
        )
        if unknown:
            self._record_run(
                case_id=request.case_id,
                task_role=ModelTaskRole.DRAFTER,
                configuration=configuration,
                rendered_input=request.rendered_input,
                raw_text=raw.text,
                duration_ms=raw.duration_ms,
                succeeded=False,
                reason_code=ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE.value,
            )
            raise ModelAdapterError(
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                detail="draft proposed an evidence id that was never admitted",
            )

        run = self._record_run(
            case_id=request.case_id,
            task_role=ModelTaskRole.DRAFTER,
            configuration=configuration,
            rendered_input=request.rendered_input,
            raw_text=raw.text,
            duration_ms=raw.duration_ms,
            succeeded=True,
            reason_code=None,
        )
        return GatewayOutcome(run=run, draft=response)

    def verify(self, request: VerificationRequest) -> GatewayOutcome:
        raw = self._invoke(
            task_role=ModelTaskRole.VERIFIER,
            case_id=request.case_id,
            rendered_input=request.rendered_input,
            call=lambda: self.adapter.verify(request),
        )
        configuration = self.verify_configuration
        parsed = self._parse_recording(
            raw, ModelTaskRole.VERIFIER, configuration, request.case_id, request.rendered_input
        )
        try:
            response = VerificationResponse.model_validate(parsed)
        except ValidationError as exc:
            self._record_run(
                case_id=request.case_id,
                task_role=ModelTaskRole.VERIFIER,
                configuration=configuration,
                rendered_input=request.rendered_input,
                raw_text=raw.text,
                duration_ms=raw.duration_ms,
                succeeded=False,
                reason_code=ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE.value,
            )
            raise ModelAdapterError(
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                raw_output_chars=len(raw.text),
                detail="verification response failed closed-schema validation",
            ) from exc

        drafted_refs = {claim.claim_ref for claim in request.draft_claims}
        verified_refs = {claim.claim_ref for claim in response.verified_claims}
        if verified_refs != drafted_refs:
            self._record_run(
                case_id=request.case_id,
                task_role=ModelTaskRole.VERIFIER,
                configuration=configuration,
                rendered_input=request.rendered_input,
                raw_text=raw.text,
                duration_ms=raw.duration_ms,
                succeeded=False,
                reason_code=ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE.value,
            )
            raise ModelAdapterError(
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                detail="the verifier did not return exactly one verdict per drafted claim",
            )

        run = self._record_run(
            case_id=request.case_id,
            task_role=ModelTaskRole.VERIFIER,
            configuration=configuration,
            rendered_input=request.rendered_input,
            raw_text=raw.text,
            duration_ms=raw.duration_ms,
            succeeded=True,
            reason_code=None,
        )
        return GatewayOutcome(run=run, verification=response)
