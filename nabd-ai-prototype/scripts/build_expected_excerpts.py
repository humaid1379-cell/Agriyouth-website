#!/usr/bin/env python3
"""Freeze the expected citations for the benign TEVV scenarios.

Citation-location accuracy is only measurable against a frozen expectation. This tool runs
the benign scenarios once and records, for each material claim, the exact source version,
page, section heading and character offsets its citations resolved to. The result is
committed and asserted by ``tests/test_expected_excerpts.py``, so a retrieval, ranking or
claim-selection change that silently moves a citation fails the suite instead of quietly
redefining the expectation.

Regenerating this file is a deliberate act. Review the diff: it is the record of which
passage the prototype says answers each question.

Usage:
    python scripts/build_expected_excerpts.py [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.domain.canonical import canonical_sha256  # noqa: E402
from app.domain.enums import Materiality  # noqa: E402
from app.domain.ids import new_case_id  # noqa: E402
from app.domain.versions import CORPUS_VERSION  # noqa: E402
from app.repositories.database import session_scope  # noqa: E402
from app.services.fixtures import (  # noqa: E402
    load_corpus_fixtures,
    load_use_case_contract,
    primary_authorization,
)
from app.services.identity import assertion_for_fixture  # noqa: E402
from app.services.orchestrator import build_case_row, process_case  # noqa: E402

OUTPUT_PATH = REPO_ROOT / "data" / CORPUS_VERSION / "expected_excerpts.json"

#: Scenarios whose citations are frozen. Only benign scenarios produce a packet.
FROZEN_SCENARIOS = ("B-01", "B-02")


def _plan() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(
        (REPO_ROOT / "data" / CORPUS_VERSION / "test_cases.json").read_text(
            encoding="utf-8"
        )
    )
    return payload


def build() -> dict[str, Any]:
    plan = _plan()
    questions = plan["questions"]
    scenarios = {entry["id"]: entry for entry in plan["scenarios"]}

    expectations: list[dict[str, Any]] = []
    with session_scope() as session:
        for scenario_id in FROZEN_SCENARIOS:
            scenario = scenarios[scenario_id]
            question = str(questions[scenario["question_key"]])
            identity = assertion_for_fixture(str(scenario["identity"]))
            case = build_case_row(
                case_id=new_case_id(),
                identity=identity,
                raw_question=question,
                authorization_id=primary_authorization().authorization_id,
                use_case_contract_id=load_use_case_contract().use_case_contract_id,
            )
            session.add(case)
            session.flush()
            result = process_case(session, case, identity)
            if result.packet is None:
                raise SystemExit(
                    f"{scenario_id} did not produce a packet; cannot freeze it"
                )

            claims = []
            for claim in sorted(result.claims, key=lambda item: item.claim_ref):
                claims.append(
                    {
                        "claim_ref": claim.claim_ref,
                        "materiality": claim.materiality.value,
                        "support_state": claim.support_state.value,
                        "statement": claim.statement,
                        "citations": [
                            {
                                "source_key": f"{link.source_id}@{link.source_version}",
                                "page_number": link.page_number,
                                "section_heading": link.section_heading,
                                "char_start": link.char_start,
                                "char_end": link.char_end,
                                "quoted_text": link.quoted_text,
                            }
                            for link in claim.evidence_links
                        ],
                    }
                )

            expectations.append(
                {
                    "scenario_id": scenario_id,
                    "question_key": scenario["question_key"],
                    "question": question,
                    "route": result.route.value,
                    "admitted_source_keys": sorted(
                        {f"{e.source_id}@{e.source_version}" for e in result.excerpts}
                    ),
                    "admitted_excerpt_count": len(result.excerpts),
                    "material_claim_count": sum(
                        1
                        for claim in result.claims
                        if claim.materiality is Materiality.MATERIAL
                    ),
                    "claims": claims,
                }
            )

    document: dict[str, Any] = {
        "expected_excerpts_version": "1.0.0",
        "corpus_id": CORPUS_VERSION,
        "corpus_manifest_sha256": load_corpus_fixtures().manifest_sha256,
        "notice": (
            "Frozen expected citations for the benign scenarios. Each material claim must "
            "resolve to the exact source version, page and character offsets recorded here. "
            "A change to retrieval, ranking or claim selection that moves a citation fails "
            "the citation-accuracy test rather than silently redefining the expectation."
        ),
        "generated_by": "scripts/build_expected_excerpts.py",
        "expectations": expectations,
    }
    document["expected_excerpts_sha256"] = canonical_sha256(document)
    return document


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if the committed file differs"
    )
    args = parser.parse_args()

    document = build()
    rendered = render(document)

    if args.check:
        if not OUTPUT_PATH.exists():
            print("expected_excerpts.json is missing", file=sys.stderr)
            return 1
        if OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            print(
                "expected_excerpts.json is out of date; review the diff, then run "
                "scripts/build_expected_excerpts.py",
                file=sys.stderr,
            )
            return 1
        print("expected_excerpts.json is current")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print(f"expected_excerpts_sha256={document['expected_excerpts_sha256']}")
    for expectation in document["expectations"]:
        print(
            f"  {expectation['scenario_id']}: {expectation['material_claim_count']} material "
            f"claim(s) across {len(expectation['admitted_source_keys'])} source(s)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
