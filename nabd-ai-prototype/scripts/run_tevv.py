#!/usr/bin/env python3
"""Execute the frozen synthetic TEVV suite and write a raw evidence report.

Results are reported as exact numerators and denominators with per-scenario expected and
actual outcomes, trace ids and case ids. Percentages are never reported on their own, and
a scenario that did not execute is recorded as ``NOT_RUN`` or ``BLOCKED`` rather than
omitted.

Executing this script produces developer-verification evidence only (gate G-A). It does
not constitute independent TEVV (gate G-D): an evaluator independent of the code author
must review and accept the output.

Usage:
    python scripts/run_tevv.py [--scenario B-01 --scenario D-01] [--output DIR] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.domain.canonical import canonical_sha256, utc_now  # noqa: E402
from app.domain.enums import TevvResultStatus  # noqa: E402
from app.repositories.database import session_scope  # noqa: E402
from app.repositories.tables import TevvResultRow  # noqa: E402
from app.services.tevv import execute_tevv_run, scenario_index  # noqa: E402

STATUS_ORDER = (
    TevvResultStatus.FAIL,
    TevvResultStatus.BLOCKED,
    TevvResultStatus.NOT_RUN,
    TevvResultStatus.PASS,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", action="append", dest="scenarios", help="scenario id filter"
    )
    parser.add_argument(
        "--executor", default="developer-verification:scripts/run_tevv.py"
    )
    parser.add_argument("--output", type=Path, default=None, help="artifact directory")
    parser.add_argument(
        "--json", action="store_true", help="print the full report as JSON"
    )
    args = parser.parse_args()

    settings = get_settings()
    output_dir = args.output or (settings.artifacts_dir / "tevv")
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog = scenario_index()
    with session_scope() as session:
        run = execute_tevv_run(
            session,
            executor=args.executor,
            scenario_ids=tuple(args.scenarios) if args.scenarios else None,
        )
        rows = list(
            session.execute(
                select(TevvResultRow)
                .where(TevvResultRow.tevv_run_id == run.tevv_run_id)
                .order_by(TevvResultRow.scenario_id.asc())
            ).scalars()
        )
        report = {
            "tevv_run_id": run.tevv_run_id,
            "plan_version": run.plan_version,
            "executor": run.executor,
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "component_versions": run.component_versions,
            "summary": run.summary,
            "independence_note": (
                "Produced by the implementation team. This is candidate developer-verification "
                "evidence (gate G-A). It is not independent TEVV (gate G-D) and it is not an "
                "acceptance of any status dimension."
            ),
            "status_dimensions": {
                "built": "NOT_EVIDENCED",
                "integration": "NOT_EVIDENCED",
                "operational": "NOT_EVIDENCED",
                "authorization": "NOT_GRANTED",
            },
            "results": [
                {
                    "scenario_id": row.scenario_id,
                    "title": catalog.get(row.scenario_id, {}).get("title", ""),
                    "category": catalog.get(row.scenario_id, {}).get("category", ""),
                    "repetition": row.repetition,
                    "status": row.status,
                    "expected": row.expected,
                    "actual": row.actual,
                    "case_id": row.case_id,
                    "trace_id": row.trace_id,
                    "defect_ids": list(row.defect_ids or ()),
                    "executed_at": row.executed_at.isoformat(),
                }
                for row in rows
            ],
        }

    report["report_sha256"] = canonical_sha256(report)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    destination = output_dir / f"tevv_report_{stamp}.json"
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"TEVV run          : {report['tevv_run_id']}")
        print(f"plan version      : {report['plan_version']}")
        print(f"scenarios in plan : {summary['scenarios_in_plan']}")
        print(f"executed          : {summary['scenarios_executed']}")
        print(
            f"pass              : {summary['numerator_pass']}/{summary['denominator']}"
        )
        print(f"failed            : {summary['failed']}")
        print(f"blocked           : {summary['blocked']}")
        print(f"not run           : {summary['not_run']}")
        print()
        by_status = {status: [] for status in STATUS_ORDER}
        for result in report["results"]:
            by_status.setdefault(TevvResultStatus(result["status"]), []).append(result)
        for status in STATUS_ORDER:
            for result in by_status.get(status, []):
                marker = "ok " if status is TevvResultStatus.PASS else "!! "
                print(
                    f"{marker}{result['scenario_id']:<8} {status.value:<8} {result['title']}"
                )
                if status is not TevvResultStatus.PASS:
                    for failure in result["actual"].get("assertion_failures", []):
                        print(f"        - {failure}")
        print()
        print(f"report            : {destination}")
        print(f"report sha256     : {report['report_sha256']}")
        print()
        print(report["independence_note"])

    summary = report["summary"]
    return 0 if summary["failed"] == 0 and summary["blocked"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
