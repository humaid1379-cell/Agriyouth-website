#!/usr/bin/env python3
"""Export the closed JSON Schema for every privileged boundary object.

Contract tests validate real payloads against these files, so a schema drifting away from
its Pydantic model is a test failure rather than a silent divergence.

Usage:
    python scripts/export_json_schemas.py [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from pydantic import BaseModel  # noqa: E402

from app.schemas.audit import AuditChainVerification, AuditEvent, KillSwitchEvent  # noqa: E402
from app.schemas.evidence import (  # noqa: E402
    EvidenceExcerpt,
    ManifestEntry,
    SourceEligibilityResult,
    SourceRecord,
)
from app.schemas.governance import (  # noqa: E402
    AuthorizationDecision,
    DemoIdentity,
    IdentityAssertion,
    StatusRecord,
    UseCaseContract,
)
from app.schemas.model_io import (  # noqa: E402
    DraftRequest,
    DraftResponse,
    ModelConfiguration,
    ModelRunRecord,
    VerificationRequest,
    VerificationResponse,
)
from app.schemas.packet import (  # noqa: E402
    DecisionReadinessPacket,
    EvidenceRecord,
    HumanDisposition,
    StopRecord,
)
from app.schemas.reasoning import (  # noqa: E402
    DefectRecord,
    DeterministicResult,
    GeneratedClaim,
    RiskProfile,
    UncertaintyRecord,
)

OUTPUT_DIR = REPO_ROOT / "contracts" / "jsonschema"

EXPORTS: tuple[tuple[str, type[BaseModel]], ...] = (
    ("authorization-decision-v1", AuthorizationDecision),
    ("use-case-contract-v1", UseCaseContract),
    ("demo-identity-v1", DemoIdentity),
    ("identity-assertion-v1", IdentityAssertion),
    ("source-record-v1", SourceRecord),
    ("source-eligibility-result-v1", SourceEligibilityResult),
    ("manifest-entry-v1", ManifestEntry),
    ("evidence-excerpt-v1", EvidenceExcerpt),
    ("model-configuration-v1", ModelConfiguration),
    ("draft-request-v1", DraftRequest),
    ("draft-response-v1", DraftResponse),
    ("verification-request-v1", VerificationRequest),
    ("verification-response-v1", VerificationResponse),
    ("model-run-record-v1", ModelRunRecord),
    ("generated-claim-v1", GeneratedClaim),
    ("deterministic-result-v1", DeterministicResult),
    ("uncertainty-record-v1", UncertaintyRecord),
    ("risk-profile-v1", RiskProfile),
    ("decision-readiness-packet-v1", DecisionReadinessPacket),
    ("human-disposition-v1", HumanDisposition),
    ("stop-record-v1", StopRecord),
    ("audit-event-v1", AuditEvent),
    ("audit-chain-verification-v1", AuditChainVerification),
    ("kill-switch-event-v1", KillSwitchEvent),
    ("evidence-record-v1", EvidenceRecord),
    ("status-record-v1", StatusRecord),
    ("defect-record-v1", DefectRecord),
)


def render(schema_id: str, model: type[BaseModel]) -> str:
    schema = model.model_json_schema(mode="serialization")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"https://nabd.local/contracts/jsonschema/{schema_id}.json"
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if a committed schema differs")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for schema_id, model in EXPORTS:
        path = OUTPUT_DIR / f"{schema_id}.json"
        rendered = render(schema_id, model)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered:
                stale.append(schema_id)
        else:
            path.write_text(rendered, encoding="utf-8")

    if args.check:
        if stale:
            print("stale JSON schemas: " + ", ".join(sorted(stale)), file=sys.stderr)
            print("run: python scripts/export_json_schemas.py", file=sys.stderr)
            return 1
        print(f"all {len(EXPORTS)} JSON schemas are current")
        return 0

    print(f"wrote {len(EXPORTS)} JSON schemas to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
