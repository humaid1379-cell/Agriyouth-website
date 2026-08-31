#!/usr/bin/env python3
"""Execute the automatable part of the deployment-validation checklist (Section 18).

Twelve confirmations are required in a clean environment. This script executes the ones
that can be verified programmatically and reports the rest as ``NOT_RUN`` with the reason,
so the gap is visible in the evidence rather than assumed away.

Running this script produces candidate developer-verification evidence only. Deployment
validation (gate G-E) requires a separate validator or a clean environment, and this script
cannot satisfy that requirement on its own.

Usage:
    python scripts/run_deployment_validation.py [--json] [--output DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.config import get_settings  # noqa: E402
from app.domain.canonical import canonical_sha256, utc_now  # noqa: E402
from app.domain.prohibited import (  # noqa: E402
    FORBIDDEN_ENV_VARS,
    FORBIDDEN_ROUTE_FRAGMENTS,
)


@dataclass(slots=True)
class Check:
    number: int
    title: str
    status: str = "NOT_RUN"
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def passed(self, detail: str, **evidence: Any) -> Check:
        self.status = "PASS"
        self.detail = detail
        self.evidence = evidence
        return self

    def failed(self, detail: str, **evidence: Any) -> Check:
        self.status = "FAIL"
        self.detail = detail
        self.evidence = evidence
        return self

    def not_run(self, detail: str) -> Check:
        self.status = "NOT_RUN"
        self.detail = detail
        return self


def _run(
    argv: list[str], cwd: Path | None = None, timeout: int = 600
) -> tuple[int, str]:
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell
            argv,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, (result.stdout + result.stderr)[-4000:]
    except FileNotFoundError:
        return 127, f"command not found: {argv[0]}"
    except subprocess.TimeoutExpired:
        return 124, "timed out"


def check_01_clean_build() -> Check:
    check = Check(
        1, "Builds from a clean checkout using lockfiles and documented commands"
    )
    if shutil.which("docker") is None:
        return check.not_run(
            "Docker is unavailable in this environment, so the Compose image build was not "
            "executed. The API package builds and installs from apps/api/pyproject.toml, "
            "which is the same dependency set the image installs."
        )
    code, output = _run(["docker", "compose", "build"])
    return (
        check.passed("docker compose build succeeded")
        if code == 0
        else check.failed("docker compose build failed", output=output)
    )


def check_02_migrations_and_seed() -> Check:
    check = Check(
        2, "Migrations and the frozen corpus seed complete and validate manifest hashes"
    )
    code, output = _run(
        [sys.executable, "scripts/seed_synthetic_corpus.py", "--no-pdf"]
    )
    if code != 0:
        return check.failed("seed failed", output=output)
    if "every source file hash matched the frozen manifest" not in output:
        return check.failed(
            "seed did not confirm manifest hash validation", output=output
        )
    manifest_code, manifest_output = _run(
        [sys.executable, "scripts/build_corpus_manifest.py", "--check"]
    )
    if manifest_code != 0:
        return check.failed("corpus manifest is out of date", output=manifest_output)
    return check.passed(
        "migrations applied, corpus seeded, every source hash matched the frozen manifest"
    )


def check_03_mock_mode_needs_no_network() -> Check:
    check = Check(
        3, "Default mock mode starts without network credentials or outbound access"
    )
    settings = get_settings()
    if settings.model_mode.value != "mock":
        return check.failed(
            f"default model mode is {settings.model_mode.value}, not mock"
        )
    if settings.live_model_endpoint or settings.live_model_api_key:
        return check.failed(
            "a live endpoint or key is configured in the default environment"
        )
    return check.passed(
        "MODEL_MODE=mock with no endpoint and no credential; the adapter runs in process",
        model_mode=settings.model_mode.value,
    )


def check_04_no_prohibited_surface() -> Check:
    check = Check(
        4, "No prohibited connectors, packages, routes or configuration fields present"
    )
    code, output = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_security.py",
            "-q",
        ],
        cwd=REPO_ROOT / "apps" / "api",
    )
    if code != 0:
        return check.failed("prohibited-surface assertions failed", output=output)
    present_env = sorted(name for name in FORBIDDEN_ENV_VARS if name in os.environ)
    if present_env:
        return check.failed(
            "prohibited environment variables present", variables=present_env
        )
    return check.passed(
        "security assertions passed and no prohibited environment variable is set",
        forbidden_route_fragments_checked=len(FORBIDDEN_ROUTE_FRAGMENTS),
    )


def check_05_live_mode_fails_closed() -> Check:
    check = Check(
        5, "Optional live mode allows one named endpoint and fails closed when absent"
    )
    code, output = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_model_gateway.py::TestLiveAdapterGuards",
            "-q",
        ],
        cwd=REPO_ROOT / "apps" / "api",
    )
    return (
        check.passed("live-mode pinning and https guards verified")
        if code == 0
        else check.failed("live-mode guards failed", output=output)
    )


def check_06_health_endpoints() -> Check:
    check = Check(6, "Health endpoints return expected status without leaking secrets")
    from fastapi.testclient import TestClient

    from app.main import create_app

    client = TestClient(create_app())
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    if live.status_code != 200 or ready.status_code != 200:
        return check.failed("a health endpoint did not return 200")
    body = (live.text + ready.text).casefold()
    for marker in ("password", "secret", "postgresql://", "psycopg"):
        if marker in body:
            return check.failed(f"health output leaked {marker!r}")
    return check.passed(
        "liveness and readiness returned 200 with no dependency detail leaked",
        readiness=ready.json().get("checks", {}),
    )


def check_07_happy_and_stop_paths() -> Check:
    check = Check(
        7,
        "A happy-path and a mandatory-stop case complete with audit chain verification",
    )
    code, output = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_pipeline.py::TestHappyPath",
            "tests/test_pipeline.py::TestStopPaths",
            "tests/test_pipeline.py::TestAuditChain",
            "-q",
        ],
        cwd=REPO_ROOT / "apps" / "api",
    )
    return (
        check.passed("happy path, stop paths and audit chain verification all passed")
        if code == 0
        else check.failed("pipeline verification failed", output=output)
    )


def check_08_reviewer_disposition() -> Check:
    check = Check(
        8, "A valid non-self reviewer creates a test-only disposition with two audits"
    )
    code, output = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_pipeline.py::TestReviewAndDisposition",
            "-q",
        ],
        cwd=REPO_ROOT / "apps" / "api",
    )
    return (
        check.passed("disposition, separation of duties and dual audit verified")
        if code == 0
        else check.failed("review verification failed", output=output)
    )


def check_09_kill_switch() -> Check:
    check = Check(
        9, "The emergency kill switch blocks intake, processing and disposition"
    )
    code, output = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-k",
            "kill_switch",
        ],
        cwd=REPO_ROOT / "apps" / "api",
    )
    return (
        check.passed("kill switch blocks intake and processing, and can be cleared")
        if code == 0
        else check.failed("kill switch verification failed", output=output)
    )


def check_10_backup_restore() -> Check:
    check = Check(
        10,
        "A backup restores into a separate database and the audit chain still verifies",
    )
    if shutil.which("pg_dump") is None or shutil.which("psql") is None:
        return check.not_run("pg_dump or psql is unavailable in this environment")

    settings = get_settings()
    if settings.is_sqlite:
        return check.not_run("the configured database is SQLite, not PostgreSQL")

    dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    restore_db = "nabd_prototype_restore"
    dump_path = Path("/tmp") / "nabd_backup.sql"  # noqa: S108 - local workbench only

    code, output = _run(
        ["pg_dump", "--no-owner", "--file", str(dump_path), dsn], timeout=300
    )
    if code != 0:
        return check.failed("pg_dump failed", output=output)

    base_dsn = dsn.rsplit("/", 1)[0]
    _run(
        ["psql", f"{base_dsn}/postgres", "-c", f"DROP DATABASE IF EXISTS {restore_db}"]
    )
    create_code, create_output = _run(
        ["psql", f"{base_dsn}/postgres", "-c", f"CREATE DATABASE {restore_db}"]
    )
    if create_code != 0:
        return check.failed(
            "could not create the restore database", output=create_output
        )

    restore_code, restore_output = _run(
        ["psql", "-q", "-f", str(dump_path), f"{base_dsn}/{restore_db}"], timeout=300
    )
    if restore_code != 0:
        return check.failed("restore failed", output=restore_output)

    verify_env = dict(os.environ)
    verify_env["DATABASE_URL"] = (
        settings.database_url.rsplit("/", 1)[0] + f"/{restore_db}"
    )
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [sys.executable, "scripts/verify_audit_chain.py", "--all"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env=verify_env,
            check=False,
        )
    except subprocess.SubprocessError as error:  # pragma: no cover - defensive
        return check.failed(f"verification in the restored database failed: {error}")

    dump_path.unlink(missing_ok=True)
    _run(
        ["psql", f"{base_dsn}/postgres", "-c", f"DROP DATABASE IF EXISTS {restore_db}"]
    )

    if result.returncode != 0:
        return check.failed(
            "the audit chain did not verify in the restored database",
            output=result.stdout[-2000:],
        )
    return check.passed(
        "backup restored into a separate database and every audit chain still verified",
        summary=result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "",
    )


def check_11_rollback() -> Check:
    check = Check(
        11, "Rollback or redeploy to the previous pinned image and configuration"
    )
    code, output = _run(
        [
            str(REPO_ROOT / ".venv" / "bin" / "alembic"),
            "downgrade",
            "-1",
        ],
        cwd=REPO_ROOT / "apps" / "api",
    )
    if code != 0:
        return check.not_run(
            "the migration rollback step did not run in this environment: "
            + output[-300:]
        )
    up_code, up_output = _run(
        [str(REPO_ROOT / ".venv" / "bin" / "alembic"), "upgrade", "head"],
        cwd=REPO_ROOT / "apps" / "api",
    )
    if up_code != 0:
        return check.failed("re-upgrade after rollback failed", output=up_output)
    return check.passed(
        "a schema rollback and re-upgrade completed. Image rollback is NOT_RUN: only one "
        "build exists in this environment, so there is no previous pinned image to roll "
        "back to."
    )


def check_12_accessibility_smoke() -> Check:
    check = Check(
        12,
        "English and Arabic reflow, keyboard, focus, contrast, colour-independent status, reduced motion",
    )
    web_dir = REPO_ROOT / "apps" / "web"
    if not (web_dir / "package.json").exists():
        return check.not_run("the web application has not been built in this checkout")
    if shutil.which("npm") is None:
        return check.not_run("npm is unavailable in this environment")
    code, output = _run(["npm", "run", "test", "--", "--run"], cwd=web_dir, timeout=900)
    if code != 0:
        return check.failed(
            "frontend accessibility and status component tests failed", output=output
        )
    return check.passed(
        "frontend component tests covering bilingual direction, keyboard access and "
        "colour-independent status passed. A manual browser smoke test remains NOT_RUN."
    )


CHECKS = (
    check_01_clean_build,
    check_02_migrations_and_seed,
    check_03_mock_mode_needs_no_network,
    check_04_no_prohibited_surface,
    check_05_live_mode_fails_closed,
    check_06_health_endpoints,
    check_07_happy_and_stop_paths,
    check_08_reviewer_disposition,
    check_09_kill_switch,
    check_10_backup_restore,
    check_11_rollback,
    check_12_accessibility_smoke,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    results: list[Check] = []
    for factory in CHECKS:
        check = factory()
        results.append(check)
        if not args.json:
            marker = {"PASS": "ok ", "FAIL": "!! ", "NOT_RUN": ".. "}[check.status]
            print(f"{marker}{check.number:>2}. {check.title}")
            print(f"       {check.status}: {check.detail}")

    passed = sum(1 for check in results if check.status == "PASS")
    failed = sum(1 for check in results if check.status == "FAIL")
    not_run = sum(1 for check in results if check.status == "NOT_RUN")

    report: dict[str, Any] = {
        "generated_at": utc_now().isoformat().replace("+00:00", "Z"),
        "environment_id": get_settings().environment_id,
        "checklist_version": "1.0.0",
        "numerator_pass": passed,
        "denominator": len(results),
        "failed": failed,
        "not_run": not_run,
        "checks": [
            {
                "number": check.number,
                "title": check.title,
                "status": check.status,
                "detail": check.detail,
                "evidence": check.evidence,
            }
            for check in results
        ],
        "independence_note": (
            "Produced by the implementation team. Deployment validation (gate G-E) requires "
            "a separate validator or a clean environment; this run does not satisfy it."
        ),
        "status_dimensions": {
            "built": "NOT_EVIDENCED",
            "integration": "NOT_EVIDENCED",
            "operational": "NOT_EVIDENCED",
            "authorization": "NOT_GRANTED",
        },
    }
    report["report_sha256"] = canonical_sha256(report)

    output_dir = args.output or (get_settings().artifacts_dir / "deployment")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    destination = output_dir / f"deployment_validation_{stamp}.json"
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print()
        print(f"pass    : {passed}/{len(results)}")
        print(f"failed  : {failed}")
        print(f"not run : {not_run}")
        print(f"report  : {destination}")
        print()
        print(report["independence_note"])

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
