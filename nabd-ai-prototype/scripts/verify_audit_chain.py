#!/usr/bin/env python3
"""Recompute a case audit chain and report the first divergence.

Verification recomputes every event hash from its stored payload and checks that each
event binds the previous one. A pass means the log is internally consistent; it does not
mean the log is complete, and it is not proof that the recorded facts are true.

Usage:
    python scripts/verify_audit_chain.py --case-id CASE-...
    python scripts/verify_audit_chain.py --all
    python scripts/verify_audit_chain.py --global
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from sqlalchemy import select  # noqa: E402

from app.repositories.database import session_scope  # noqa: E402
from app.repositories.tables import CaseRow  # noqa: E402
from app.services.audit import verify_chain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case-id", help="verify one case chain")
    group.add_argument("--all", action="store_true", help="verify every case chain")
    group.add_argument(
        "--global",
        dest="global_chain",
        action="store_true",
        help="verify the non-case chain",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable output"
    )
    args = parser.parse_args()

    reports: list[dict[str, object]] = []
    with session_scope() as session:
        if args.all:
            case_ids = list(session.execute(select(CaseRow.case_id)).scalars())
        elif args.global_chain:
            case_ids = [None]  # type: ignore[list-item]
        else:
            case_ids = [args.case_id]

        for case_id in case_ids:
            reports.append(verify_chain(session, case_id).model_dump(mode="json"))

    failures = [report for report in reports if not report["verified"]]
    if args.json:
        print(json.dumps({"reports": reports, "failures": len(failures)}, indent=2))
    else:
        for report in reports:
            label = report["case_id"] or "GLOBAL"
            status = "VERIFIED" if report["verified"] else "DIVERGENT"
            print(f"{status:<10} {label}  events={report['event_count']}")
            if not report["verified"]:
                print(
                    f"           first divergence at sequence "
                    f"{report['first_divergence_sequence']} "
                    f"({report['first_divergence_kind']}, "
                    f"event {report['first_divergence_event_id']})"
                )
        print(f"\n{len(reports) - len(failures)}/{len(reports)} chains verified")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
