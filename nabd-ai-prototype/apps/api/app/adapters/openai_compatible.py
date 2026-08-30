"""Optional live adapter for exactly one pinned OpenAI-compatible endpoint.

Disabled unless ``MODEL_MODE=live`` and every explicit pinning variable is present. It may
call exactly one configured endpoint and model. It does not discover models, does not use
tools, does not browse, does not retry a different model and does not fall back.

The default build never constructs this class, so the container runs with no outbound
internet access at all.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from app.adapters.protocol import ModelAdapterError, RawModelResponse
from app.config import Settings
from app.domain.enums import ModelMode, Severity
from app.domain.reason_codes import ReasonCode
from app.schemas.model_io import DraftRequest, ModelConfiguration, VerificationRequest
from app.services.prompts import load_prompt


class OpenAICompatibleAdapter:
    """Single-endpoint, single-model, no-tools, no-fallback transport."""

    name = "OpenAICompatibleAdapter"
    supports_tool_calling = False
    supports_fallback = False

    def __init__(
        self,
        settings: Settings,
        draft_configuration: ModelConfiguration,
        verify_configuration: ModelConfiguration,
    ) -> None:
        if settings.model_mode is not ModelMode.LIVE:
            raise ModelAdapterError(
                ReasonCode.MODEL_CONFIGURATION_MISMATCH,
                detail="live adapter constructed while MODEL_MODE is not live",
            )
        endpoint = settings.live_model_endpoint or ""
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ModelAdapterError(
                ReasonCode.MODEL_CONFIGURATION_MISMATCH,
                detail="live endpoint must be a single https URL",
            )
        self._endpoint = endpoint
        self._allowed_host = parsed.netloc
        self._model = settings.live_model_name or ""
        self._api_key = settings.live_model_api_key
        self._draft_configuration = draft_configuration
        self._verify_configuration = verify_configuration

    # -- transport ---------------------------------------------------------------
    def _call(self, prompt: str, rendered_input: str, configuration: ModelConfiguration) -> RawModelResponse:
        if urlparse(self._endpoint).netloc != self._allowed_host:  # pragma: no cover - defensive
            raise ModelAdapterError(
                ReasonCode.MODEL_FALLBACK_ATTEMPTED,
                severity=Severity.S0_CRITICAL,
                detail="endpoint host changed after pinning",
            )
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": rendered_input},
            ],
            "temperature": configuration.temperature_milli / 1000,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"},
            # Tool calling is explicitly off. The output schema also rejects tool requests.
            "tools": [],
            "tool_choice": "none",
            "stream": False,
        }
        request = urllib.request.Request(  # noqa: S310 - scheme is validated as https above
            self._endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(  # noqa: S310 - single pinned https endpoint
                request, timeout=configuration.timeout_seconds
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise ModelAdapterError(ReasonCode.MODEL_TIMEOUT) from exc
        except urllib.error.URLError as exc:
            raise ModelAdapterError(ReasonCode.MODEL_UNAVAILABLE) from exc
        except json.JSONDecodeError as exc:
            raise ModelAdapterError(ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE) from exc

        duration_ms = int((time.monotonic() - started) * 1000)
        returned_model = str(payload.get("model", ""))
        if returned_model and returned_model != self._model:
            raise ModelAdapterError(
                ReasonCode.MODEL_CONFIGURATION_MISMATCH,
                severity=Severity.S0_CRITICAL,
                detail="the endpoint answered with a different model than the pinned one",
            )
        choices = payload.get("choices") or []
        if not choices:
            raise ModelAdapterError(ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE)
        message = choices[0].get("message", {})
        if message.get("tool_calls"):
            raise ModelAdapterError(
                ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE,
                severity=Severity.S0_CRITICAL,
                detail="the endpoint returned a tool call, which V1 forbids",
            )
        content = message.get("content")
        if not isinstance(content, str):
            raise ModelAdapterError(ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE)
        return RawModelResponse(content, duration_ms, returned_model or self._model)

    def draft(self, request: DraftRequest) -> RawModelResponse:
        return self._call(load_prompt("draft_v1.md"), request.rendered_input, self._draft_configuration)

    def verify(self, request: VerificationRequest) -> RawModelResponse:
        return self._call(
            load_prompt("verify_v1.md"), request.rendered_input, self._verify_configuration
        )
