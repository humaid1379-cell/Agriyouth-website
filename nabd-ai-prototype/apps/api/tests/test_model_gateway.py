"""Slice 5: model gateway, adapters, prompts and the two-call budget."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.adapters.mock_adapter import DeterministicMockAdapter
from app.adapters.protocol import ModelAdapterError, ModelFault, RawModelResponse
from app.domain.enums import DataClassification, ModelMode, ModelTaskRole, TrustLabel
from app.domain.limits import (
    DRAFT_INPUT_MAX_CHARS,
    MODEL_CALLS_MAX,
    MODEL_OUTPUT_MAX_CHARS,
    SAME_ENDPOINT_RETRY_MAX,
)
from app.domain.reason_codes import ReasonCode
from app.schemas.evidence import EvidenceExcerpt
from app.schemas.model_io import DraftRequest, VerificationRequest
from app.services.fixtures import active_model_configuration
from app.services.model_gateway import CallBudget, ModelBudgetExceeded, ModelGateway
from app.services.prompts import (
    PROMPT_FORBIDDEN_MARKERS,
    build_draft_input,
    load_prompt,
    prompt_contains_forbidden_marker,
)

pytestmark = pytest.mark.unit

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "app" / "prompts"

QUESTION = "What evidence must accompany an internal policy exception request?"

BODY = (
    "An internal policy exception request is incomplete, and shall not proceed to review, "
    "unless the exception file contains all three of the following mandatory evidence items. "
    "A Tier 2 request shall be reviewed by a manager grade reviewer."
)


def _excerpt(index: int = 0, text: str = BODY) -> EvidenceExcerpt:
    return EvidenceExcerpt(
        produced_by="test",
        excerpt_id=f"EXC-test-{index:03d}",
        case_id="CASE-gateway",
        source_id="POL-001",
        source_version="v1",
        page_number=2,
        section_heading="3. Evidence Requirements",
        block_index=index,
        char_start=100 + index,
        char_end=100 + index + len(text),
        text=text,
        text_sha256="a" * 64,
        source_sha256="b" * 64,
        rank=index,
        trust_label=TrustLabel.UNTRUSTED_CONTENT,
        data_classification=DataClassification.SYNTHETIC_UNTRUSTED_CONTENT,
    )


def _gateway(fault: ModelFault = ModelFault.NONE) -> ModelGateway:
    return ModelGateway(
        adapter=DeterministicMockAdapter(fault=fault),
        draft_configuration=active_model_configuration(ModelTaskRole.DRAFTER),
        verify_configuration=active_model_configuration(ModelTaskRole.VERIFIER),
        mode=ModelMode.MOCK,
    )


def _draft_request(excerpts=None) -> DraftRequest:  # type: ignore[no-untyped-def]
    excerpts = excerpts or (_excerpt(),)
    return DraftRequest(
        case_id="CASE-gateway",
        normalised_question=QUESTION,
        permitted_purpose="INTERNAL_POLICY_SOP_EVIDENCE_LOOKUP",
        output_schema_id="draft-response-v1",
        prompt_version="prompt-draft-v1.0.0",
        excerpts=excerpts,
        rendered_input=build_draft_input(
            normalised_question=QUESTION,
            permitted_purpose="INTERNAL_POLICY_SOP_EVIDENCE_LOOKUP",
            excerpts=excerpts,
        ),
    )


class TestPromptContracts:
    def test_both_prompt_files_exist_and_are_versioned(self) -> None:
        for name, version in (
            ("draft_v1.md", "prompt-draft-v1.0.0"),
            ("verify_v1.md", "prompt-verify-v1.0.0"),
        ):
            text = load_prompt(name)
            assert version in text

    def test_prompts_declare_excerpts_untrusted(self) -> None:
        for name in ("draft_v1.md", "verify_v1.md"):
            text = load_prompt(name).casefold()
            assert "untrusted data" in text
            assert "ignore them" in text

    def test_prompts_contain_no_secret_route_or_tool_instruction(self) -> None:
        for name in ("draft_v1.md", "verify_v1.md"):
            found = prompt_contains_forbidden_marker(load_prompt(name))
            assert found == (), f"{name} contains forbidden markers {found}"

    def test_forbidden_marker_list_is_non_empty(self) -> None:
        assert PROMPT_FORBIDDEN_MARKERS

    def test_prompts_forbid_route_and_approval_language(self) -> None:
        for name in ("draft_v1.md", "verify_v1.md"):
            # Prose wraps across lines, so compare against whitespace-normalised text.
            text = " ".join(load_prompt(name).casefold().split())
            assert "you do not decide a route" in text
            assert "do not approve, execute, transmit or activate anything" in text
            assert "you do not request a tool" in text

    def test_only_two_prompt_files_exist(self) -> None:
        assert sorted(p.name for p in PROMPTS_DIR.glob("*.md")) == ["draft_v1.md", "verify_v1.md"]


class TestRenderedInput:
    def test_excerpts_are_wrapped_in_untrusted_envelopes(self) -> None:
        rendered = _draft_request().rendered_input
        assert "<<<UNTRUSTED_CONTENT id=EXC-test-000" in rendered
        assert "<<<END_UNTRUSTED_CONTENT id=EXC-test-000>>>" in rendered

    def test_over_long_input_is_refused_before_the_call(self) -> None:
        oversized = tuple(_excerpt(i, "y" * 1400) for i in range(8))
        with pytest.raises(ValueError, match="input limit"):
            build_draft_input(
                normalised_question="q" * (DRAFT_INPUT_MAX_CHARS),
                permitted_purpose="p",
                excerpts=oversized,
            )


class TestCallBudget:
    def test_two_calls_are_permitted_and_a_third_is_not(self) -> None:
        budget = CallBudget()
        budget.reserve(ModelTaskRole.DRAFTER)
        budget.reserve(ModelTaskRole.VERIFIER)
        assert budget.total_calls == MODEL_CALLS_MAX
        with pytest.raises(ModelBudgetExceeded) as excinfo:
            budget.reserve(ModelTaskRole.VERIFIER)
        assert excinfo.value.code is ReasonCode.MODEL_CALL_LIMIT_EXCEEDED

    def test_a_second_draft_call_is_refused(self) -> None:
        budget = CallBudget()
        budget.reserve(ModelTaskRole.DRAFTER)
        with pytest.raises(ModelBudgetExceeded):
            budget.reserve(ModelTaskRole.DRAFTER)

    def test_retry_budget_is_one(self) -> None:
        budget = CallBudget()
        budget.reserve_retry()
        assert budget.retries == SAME_ENDPOINT_RETRY_MAX
        with pytest.raises(ModelAdapterError) as excinfo:
            budget.reserve_retry()
        assert excinfo.value.code is ReasonCode.RETRY_LIMIT_EXCEEDED

    def test_no_retry_after_a_partial_result_was_accepted(self) -> None:
        budget = CallBudget()
        budget.partial_result_accepted = True
        with pytest.raises(ModelAdapterError) as excinfo:
            budget.reserve_retry()
        assert excinfo.value.code is ReasonCode.RETRY_LIMIT_EXCEEDED


class TestDeterministicMock:
    def test_draft_and_verify_produce_a_supported_exactly_located_claim(self) -> None:
        gateway = _gateway()
        draft = gateway.draft(_draft_request()).draft
        assert draft is not None
        assert draft.claims

        verification = gateway.verify(
            VerificationRequest(
                case_id="CASE-gateway",
                output_schema_id="verification-response-v1",
                prompt_version="prompt-verify-v1.0.0",
                draft_claims=draft.claims,
                excerpts=(_excerpt(),),
                rendered_input="verify",
            )
        ).verification
        assert verification is not None
        first = verification.verified_claims[0]
        assert first.support_state.value == "SUPPORTED"
        span = first.support_spans[0]
        assert BODY[span.quote_start : span.quote_end] == span.quoted_text

    def test_output_is_byte_identical_across_runs(self) -> None:
        request = _draft_request()
        first = DeterministicMockAdapter().draft(request)
        second = DeterministicMockAdapter().draft(request)
        assert first.text == second.text

    def test_mock_advertises_neither_tools_nor_fallback(self) -> None:
        adapter = DeterministicMockAdapter()
        assert adapter.supports_tool_calling is False
        assert adapter.supports_fallback is False


class TestGatewayFaultHandling:
    @pytest.mark.parametrize(
        ("fault", "expected"),
        [
            (ModelFault.DRAFT_MALFORMED, ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE),
            (ModelFault.DRAFT_REFUSAL, ReasonCode.MODEL_REFUSAL),
            (ModelFault.TOOL_REQUEST, ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE),
            (ModelFault.OVERSIZED_OUTPUT, ReasonCode.MODEL_OUTPUT_LIMIT_EXCEEDED),
            (ModelFault.FALLBACK_ATTEMPT, ReasonCode.MODEL_FALLBACK_ATTEMPTED),
        ],
    )
    def test_draft_faults_produce_typed_failures(
        self, fault: ModelFault, expected: ReasonCode
    ) -> None:
        with pytest.raises(ModelAdapterError) as excinfo:
            _gateway(fault).draft(_draft_request())
        assert excinfo.value.code is expected

    def test_timeout_retries_once_then_fails_closed(self) -> None:
        gateway = _gateway(ModelFault.DRAFT_TIMEOUT)
        with pytest.raises(ModelAdapterError) as excinfo:
            gateway.draft(_draft_request())
        assert excinfo.value.code is ReasonCode.MODEL_TIMEOUT
        assert gateway.budget.retries == SAME_ENDPOINT_RETRY_MAX
        assert gateway.budget.total_calls == 1

    def test_unavailable_endpoint_does_not_fall_back(self) -> None:
        gateway = _gateway(ModelFault.UNAVAILABLE)
        with pytest.raises(ModelAdapterError) as excinfo:
            gateway.draft(_draft_request())
        assert excinfo.value.code is ReasonCode.MODEL_UNAVAILABLE

    def test_invalid_json_is_never_coerced(self) -> None:
        with pytest.raises(ModelAdapterError):
            _gateway(ModelFault.DRAFT_MALFORMED).draft(_draft_request())

    def test_failed_calls_are_still_recorded_as_model_runs(self) -> None:
        gateway = _gateway(ModelFault.DRAFT_MALFORMED)
        with pytest.raises(ModelAdapterError):
            gateway.draft(_draft_request())
        assert gateway.runs
        assert gateway.runs[-1].succeeded is False


class TestGatewayBoundaryEnforcement:
    def test_adapter_advertising_tools_is_refused(self) -> None:
        class ToolAdapter(DeterministicMockAdapter):
            supports_tool_calling = True

        gateway = _gateway()
        gateway.adapter = ToolAdapter()
        with pytest.raises(ModelAdapterError) as excinfo:
            gateway.draft(_draft_request())
        assert excinfo.value.code is ReasonCode.MODEL_CONFIGURATION_MISMATCH

    def test_adapter_advertising_fallback_is_refused(self) -> None:
        class FallbackAdapter(DeterministicMockAdapter):
            supports_fallback = True

        gateway = _gateway()
        gateway.adapter = FallbackAdapter()
        with pytest.raises(ModelAdapterError) as excinfo:
            gateway.draft(_draft_request())
        assert excinfo.value.code is ReasonCode.MODEL_FALLBACK_ATTEMPTED

    def test_response_from_another_model_revision_is_refused(self) -> None:
        class WrongRevision(DeterministicMockAdapter):
            def draft(self, request: DraftRequest) -> RawModelResponse:  # type: ignore[override]
                original = super().draft(request)
                return RawModelResponse(original.text, original.duration_ms, "some-other-model")

        gateway = _gateway()
        gateway.adapter = WrongRevision()
        with pytest.raises(ModelAdapterError) as excinfo:
            gateway.draft(_draft_request())
        assert excinfo.value.code is ReasonCode.MODEL_CONFIGURATION_MISMATCH

    def test_draft_citing_an_unadmitted_excerpt_is_refused(self) -> None:
        class Fabricator(DeterministicMockAdapter):
            def draft(self, request: DraftRequest) -> RawModelResponse:  # type: ignore[override]
                payload = {
                    "claims": [
                        {
                            "claim_ref": "C01",
                            "statement": "invented",
                            "materiality": "MATERIAL",
                            "proposed_evidence_ids": ["EXC-not-admitted"],
                        }
                    ],
                    "assumptions": [],
                    "unresolved_points": [],
                    "draft_summary": "s",
                }
                return RawModelResponse(json.dumps(payload), 1, "deterministic-mock-1.0.0")

        gateway = _gateway()
        gateway.adapter = Fabricator()
        with pytest.raises(ModelAdapterError) as excinfo:
            gateway.draft(_draft_request())
        assert excinfo.value.code is ReasonCode.MODEL_BOUNDARY_OR_SCHEMA_FAILURE

    def test_verifier_must_return_one_verdict_per_drafted_claim(self) -> None:
        class Dropper(DeterministicMockAdapter):
            def verify(self, request: VerificationRequest) -> RawModelResponse:  # type: ignore[override]
                payload = {"verified_claims": [], "verifier_notes": ""}
                return RawModelResponse(json.dumps(payload), 1, "deterministic-mock-1.0.0")

        gateway = _gateway()
        draft = gateway.draft(_draft_request()).draft
        assert draft is not None
        gateway.adapter = Dropper()
        with pytest.raises(ModelAdapterError):
            gateway.verify(
                VerificationRequest(
                    case_id="CASE-gateway",
                    output_schema_id="verification-response-v1",
                    prompt_version="prompt-verify-v1.0.0",
                    draft_claims=draft.claims,
                    excerpts=(_excerpt(),),
                    rendered_input="verify",
                )
            )

    def test_output_limit_is_bounded_by_the_frozen_ceiling(self) -> None:
        configuration = active_model_configuration(ModelTaskRole.DRAFTER)
        assert configuration.output_limit_chars <= MODEL_OUTPUT_MAX_CHARS
        assert configuration.tool_calling_enabled is False
        assert configuration.fallback_enabled is False


class TestLiveAdapterGuards:
    def test_live_adapter_refuses_to_construct_in_mock_mode(self) -> None:
        from app.adapters.openai_compatible import OpenAICompatibleAdapter
        from app.config import Settings

        settings = Settings()  # type: ignore[call-arg]
        with pytest.raises(ModelAdapterError) as excinfo:
            OpenAICompatibleAdapter(
                settings,
                active_model_configuration(ModelTaskRole.DRAFTER),
                active_model_configuration(ModelTaskRole.VERIFIER),
            )
        assert excinfo.value.code is ReasonCode.MODEL_CONFIGURATION_MISMATCH

    def test_live_mode_requires_full_pinning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.config import Settings

        monkeypatch.setenv("MODEL_MODE", "live")
        monkeypatch.delenv("LIVE_MODEL_ENDPOINT", raising=False)
        monkeypatch.delenv("LIVE_MODEL_NAME", raising=False)
        monkeypatch.delenv("LIVE_MODEL_CONFIG_ID", raising=False)
        with pytest.raises(ValueError, match="requires explicit pinning"):
            Settings()  # type: ignore[call-arg]

    def test_live_endpoint_must_be_https(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.config import Settings

        monkeypatch.setenv("MODEL_MODE", "live")
        monkeypatch.setenv("LIVE_MODEL_ENDPOINT", "http://insecure.example/v1/chat/completions")
        monkeypatch.setenv("LIVE_MODEL_NAME", "some-model")
        monkeypatch.setenv("LIVE_MODEL_CONFIG_ID", "MC-LIVE-V1")
        with pytest.raises(ValueError, match="single https"):
            Settings()  # type: ignore[call-arg]
