"""Slice 1: schemas, enumerations, reason codes, fixtures and canonicalization."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.domain.canonical import (
    CanonicalizationError,
    canonical_dumps,
    canonical_sha256,
    compute_packet_hash,
    format_timestamp,
    normalise_text,
    utc_now,
)
from app.domain.enums import (
    CASE_STATE_STAGE,
    ORDERED_CASE_STATES,
    AuthorizationStatus,
    CaseState,
    DispositionValue,
    OperationalStatus,
    Route,
    StatusEvidence,
)
from app.domain.limits import LIMIT_REGISTER
from app.domain.notices import REQUIRED_NOTICES
from app.domain.reason_codes import REASON_MESSAGES, STATE_FAILURE_REASON, ReasonCode
from app.schemas.evidence import EvidenceExcerpt
from app.schemas.governance import AuthorizationDecision
from app.schemas.model_io import DraftClaim, DraftResponse, VerifiedClaim

CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "contracts" / "jsonschema"

pytestmark = pytest.mark.unit


class TestEnumerations:
    def test_route_has_exactly_two_values(self) -> None:
        assert {route.value for route in Route} == {"HUMAN_REVIEW_REQUIRED", "CANNOT_PROCEED"}

    def test_twenty_ordered_states_plus_terminal_stop(self) -> None:
        assert len(ORDERED_CASE_STATES) == 20
        assert len(list(CaseState)) == 21
        assert CaseState.CANNOT_PROCEED not in CASE_STATE_STAGE

    def test_stage_numbers_are_contiguous(self) -> None:
        assert sorted(CASE_STATE_STAGE.values()) == list(range(20))

    def test_dispositions_are_test_only(self) -> None:
        assert {value.value for value in DispositionValue} == {
            "RETURN_FOR_CLARIFICATION",
            "ACCEPT_AS_TEST_EVIDENCE",
            "REJECT_AS_TEST_EVIDENCE",
        }
        assert not any("APPROVE" in value.value for value in DispositionValue)

    def test_status_dimensions_default_to_unevidenced(self) -> None:
        assert StatusEvidence.NOT_EVIDENCED.value == "NOT_EVIDENCED"
        assert OperationalStatus.NOT_EVIDENCED.value == "NOT_EVIDENCED"
        assert AuthorizationStatus.NOT_GRANTED.value == "NOT_GRANTED"


class TestReasonCodes:
    def test_every_code_has_a_message(self) -> None:
        missing = [code.value for code in ReasonCode if code not in REASON_MESSAGES]
        assert missing == []

    def test_messages_do_not_leak_secrets_or_prompts(self) -> None:
        forbidden = ("password", "api_key", "secret", "bearer ", "prompt-draft-v1")
        for code, message in REASON_MESSAGES.items():
            lowered = message.casefold()
            for marker in forbidden:
                assert marker not in lowered, f"{code.value} message leaks {marker!r}"

    def test_each_ordered_state_up_to_pre_issuance_maps_to_a_failure_code(self) -> None:
        for state in ORDERED_CASE_STATES[:15]:
            assert state in STATE_FAILURE_REASON


class TestClosedSchemas:
    def test_unknown_field_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DraftClaim(
                claim_ref="C01",
                statement="x",
                materiality="MATERIAL",
                proposed_evidence_ids=("EXC-1",),
                route="HUMAN_REVIEW_REQUIRED",  # type: ignore[call-arg]
            )

    def test_draft_cannot_carry_a_route_or_authority_field(self) -> None:
        assert "route" not in DraftResponse.model_fields
        assert "authorization" not in DraftResponse.model_fields
        assert "rule_results" not in DraftResponse.model_fields

    def test_supported_claim_requires_evidence(self) -> None:
        with pytest.raises(ValidationError):
            VerifiedClaim(
                claim_ref="C01",
                support_state="SUPPORTED",
                evidence_ids=(),
                support_spans=(),
                conflict_ids=(),
            )

    def test_support_span_must_reference_a_cited_excerpt(self) -> None:
        with pytest.raises(ValidationError):
            VerifiedClaim(
                claim_ref="C01",
                support_state="SUPPORTED",
                evidence_ids=("EXC-a",),
                support_spans=(
                    {
                        "excerpt_id": "EXC-b",
                        "quote_start": 0,
                        "quote_end": 4,
                        "quoted_text": "text",
                    },
                ),
                conflict_ids=(),
            )

    def test_authorization_fixture_status_is_pinned_to_not_granted(self) -> None:
        assert (
            AuthorizationDecision.model_fields["authorization_status"].default
            is AuthorizationStatus.NOT_GRANTED
        )

    def test_excerpt_offsets_must_be_ordered(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceExcerpt(
                produced_by="test",
                excerpt_id="EXC-1",
                case_id="CASE-1",
                source_id="POL-001",
                source_version="v1",
                page_number=1,
                section_heading="h",
                block_index=0,
                char_start=10,
                char_end=10,
                text="t",
                text_sha256="0" * 64,
                source_sha256="0" * 64,
                rank=0,
            )


class TestCanonicalJson:
    def test_keys_are_sorted_and_separators_compact(self) -> None:
        assert canonical_dumps({"b": 1, "a": 2}) == '{"a":2,"b":1}'

    def test_floats_are_rejected(self) -> None:
        with pytest.raises(CanonicalizationError):
            canonical_dumps({"score": 1.5})

    def test_timestamps_render_as_utc_with_millisecond_precision(self) -> None:
        rendered = format_timestamp(datetime(2025, 3, 1, 12, 0, 0, 123456, tzinfo=UTC))
        assert rendered == "2025-03-01T12:00:00.123Z"

    def test_naive_datetime_is_rejected(self) -> None:
        with pytest.raises(CanonicalizationError):
            format_timestamp(datetime(2025, 3, 1, 12, 0, 0))

    def test_line_endings_and_unicode_are_normalised(self) -> None:
        assert normalise_text("a\r\nb") == "a\nb"
        # U+0065 U+0301 (e + combining acute) normalises to U+00E9.
        assert normalise_text("e\u0301") == "\u00e9"

    def test_hash_is_stable_across_key_order(self) -> None:
        assert canonical_sha256({"a": 1, "b": [1, 2]}) == canonical_sha256({"b": [1, 2], "a": 1})

    def test_packet_hash_omits_only_the_recorded_hash(self) -> None:
        packet = {"identity": {"case_id": "c"}, "integrity": {"packet_sha256": "x", "profile": "p"}}
        without = {"identity": {"case_id": "c"}, "integrity": {"profile": "p"}}
        assert compute_packet_hash(packet) == canonical_sha256(without)

    def test_utc_now_is_millisecond_truncated(self) -> None:
        assert utc_now().microsecond % 1000 == 0


class TestNoticesAndLimits:
    def test_four_notices_exist_with_english_and_arabic(self) -> None:
        assert len(REQUIRED_NOTICES) == 4
        for notice in REQUIRED_NOTICES:
            assert notice.text_en.strip()
            assert notice.text_ar.strip()

    def test_notices_state_non_execution(self) -> None:
        combined = " ".join(notice.text_en for notice in REQUIRED_NOTICES).casefold()
        assert "has not approved, executed, transmitted, or activated" in combined
        assert "retains final authority" in combined
        assert "synthetic data only" in combined

    def test_every_limit_has_a_failure_reason_code(self) -> None:
        for limit in LIMIT_REGISTER:
            assert isinstance(limit.reason_code, ReasonCode)
            assert limit.value > 0


class TestExportedJsonSchemas:
    def test_schema_directory_is_populated(self) -> None:
        assert list(CONTRACTS_DIR.glob("*.json")), "run scripts/export_json_schemas.py"

    def test_every_schema_is_valid_draft_2020_12(self) -> None:
        for path in sorted(CONTRACTS_DIR.glob("*.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

    def test_packet_schema_forbids_additional_properties(self) -> None:
        schema = json.loads((CONTRACTS_DIR / "decision-readiness-packet-v1.json").read_text())
        assert schema.get("additionalProperties") is False

    def test_schemas_are_current(self) -> None:
        from export_json_schemas import EXPORTS, render

        stale = [
            schema_id
            for schema_id, model in EXPORTS
            if (CONTRACTS_DIR / f"{schema_id}.json").read_text(encoding="utf-8")
            != render(schema_id, model)
        ]
        assert stale == [], "run scripts/export_json_schemas.py"
