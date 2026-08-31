"""Citation-location accuracy against the frozen expectation.

The frozen expectation in ``data/synthetic_policy_collection_v1/expected_excerpts.json``
records the exact source version, page and character offsets each material claim resolved
to. These tests re-run the benign scenarios and require the same result, so a change to
retrieval, ranking or claim selection that moves a citation fails here rather than silently
redefining what the prototype considers the answer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.domain.canonical import canonical_sha256, normalise_text
from app.domain.enums import Materiality, Route, SupportState
from app.domain.ids import new_case_id
from app.services.fixtures import (
    load_corpus_fixtures,
    load_use_case_contract,
    primary_authorization,
    source_file_path,
)
from app.services.identity import assertion_for_fixture
from app.services.orchestrator import build_case_row, process_case

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_PATH = REPO_ROOT / "data" / "synthetic_policy_collection_v1" / "expected_excerpts.json"


def _expected() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    return payload


def _plan_questions() -> dict[str, str]:
    payload = json.loads(
        (REPO_ROOT / "data" / "synthetic_policy_collection_v1" / "test_cases.json").read_text(
            encoding="utf-8"
        )
    )
    return dict(payload["questions"])


def _run(db: Session, question: str):  # type: ignore[no-untyped-def]
    identity = assertion_for_fixture("requester.analyst@demo.nabd.local")
    case = build_case_row(
        case_id=new_case_id(),
        identity=identity,
        raw_question=question,
        authorization_id=primary_authorization().authorization_id,
        use_case_contract_id=load_use_case_contract().use_case_contract_id,
    )
    db.add(case)
    db.flush()
    return process_case(db, case, identity)


class TestFrozenExpectation:
    def test_the_fixture_self_hash_matches_its_content(self) -> None:
        document = _expected()
        recorded = document.pop("expected_excerpts_sha256")
        assert recorded == canonical_sha256(document)

    def test_the_fixture_pins_the_current_corpus(self) -> None:
        assert _expected()["corpus_manifest_sha256"] == load_corpus_fixtures().manifest_sha256

    def test_every_frozen_scenario_is_a_benign_scenario(self) -> None:
        assert [item["scenario_id"] for item in _expected()["expectations"]] == ["B-01", "B-02"]


class TestCitationAccuracy:
    @pytest.mark.parametrize("scenario_id", ["B-01", "B-02"])
    def test_material_claims_resolve_to_the_frozen_citations(
        self, db: Session, scenario_id: str
    ) -> None:
        expectation = next(
            item for item in _expected()["expectations"] if item["scenario_id"] == scenario_id
        )
        result = _run(db, _plan_questions()[expectation["question_key"]])

        assert result.route is Route.HUMAN_REVIEW_REQUIRED
        actual = {
            claim.claim_ref: [
                {
                    "source_key": f"{link.source_id}@{link.source_version}",
                    "page_number": link.page_number,
                    "section_heading": link.section_heading,
                    "char_start": link.char_start,
                    "char_end": link.char_end,
                    "quoted_text": link.quoted_text,
                }
                for link in claim.evidence_links
            ]
            for claim in result.claims
        }

        for expected_claim in expectation["claims"]:
            ref = expected_claim["claim_ref"]
            assert ref in actual, f"{scenario_id} no longer produces claim {ref}"
            assert actual[ref] == expected_claim["citations"], (
                f"{scenario_id} {ref} citations moved. Review the change, then regenerate "
                "with scripts/build_expected_excerpts.py if it is intended."
            )

    @pytest.mark.parametrize("scenario_id", ["B-01", "B-02"])
    def test_frozen_citations_still_slice_the_source_exactly(self, scenario_id: str) -> None:
        expectation = next(
            item for item in _expected()["expectations"] if item["scenario_id"] == scenario_id
        )
        corpus = load_corpus_fixtures()
        for claim in expectation["claims"]:
            for citation in claim["citations"]:
                item = corpus.by_key(citation["source_key"])
                assert item is not None
                raw = normalise_text(source_file_path(item).read_text(encoding="utf-8"))
                sliced = raw[citation["char_start"] : citation["char_end"]]
                assert (
                    sliced == citation["quoted_text"]
                ), f"{citation['source_key']} offsets no longer reproduce the quoted text"

    @pytest.mark.parametrize("scenario_id", ["B-01", "B-02"])
    def test_material_claim_count_and_support_are_unchanged(
        self, db: Session, scenario_id: str
    ) -> None:
        expectation = next(
            item for item in _expected()["expectations"] if item["scenario_id"] == scenario_id
        )
        result = _run(db, _plan_questions()[expectation["question_key"]])
        material = [c for c in result.claims if c.materiality is Materiality.MATERIAL]
        assert len(material) == expectation["material_claim_count"]
        assert all(claim.support_state is SupportState.SUPPORTED for claim in material)

    def test_the_multi_source_scenario_really_cites_multiple_sources(self) -> None:
        expectation = next(
            item for item in _expected()["expectations"] if item["scenario_id"] == "B-02"
        )
        cited = {
            citation["source_key"]
            for claim in expectation["claims"]
            for citation in claim["citations"]
        }
        assert len(cited) >= 2, f"B-02 should cite two or more sources, got {sorted(cited)}"

    def test_no_ineligible_source_appears_in_any_frozen_expectation(self) -> None:
        ineligible = {"POL-001@v0", "POL-002@v1", "SOP-002@v1", "ADV-001@v1"}
        for expectation in _expected()["expectations"]:
            assert set(expectation["admitted_source_keys"]).isdisjoint(ineligible)
            for claim in expectation["claims"]:
                for citation in claim["citations"]:
                    assert citation["source_key"] not in ineligible
