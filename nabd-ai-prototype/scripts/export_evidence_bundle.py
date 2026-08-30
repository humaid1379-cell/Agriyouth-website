#!/usr/bin/env python3
"""Assemble a timestamped evidence bundle with a manifest and SHA-256 checksums.

The bundle is an inventory of what exists, with hashes so that a separate reviewer can
confirm nothing changed between production and review. It records the four status
dimensions at their defaults and makes no acceptance claim: only a human owner, separate
from the preparer and the evaluator, can accept a narrow status claim.

Usage:
    python scripts/export_evidence_bundle.py [--output DIR] [--include-tevv]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.config import get_settings  # noqa: E402
from app.domain.canonical import canonical_sha256, file_sha256, utc_now  # noqa: E402
from app.domain.versions import COMPONENT_VERSIONS, ENVIRONMENT_ID  # noqa: E402
from app.rules.catalog import catalog_payload  # noqa: E402
from app.services.fixtures import load_corpus_fixtures  # noqa: E402

#: Repository artifacts always inventoried, relative to the project root.
TRACKED_PATHS: tuple[str, ...] = (
    "README.md",
    "SECURITY_BOUNDARIES.md",
    "PROTOTYPE_STATUS.md",
    "docker-compose.yml",
    "Makefile",
    ".env.example",
    "docs",
    "contracts",
    "data/synthetic_policy_collection_v1",
    "data/fixtures",
    "artifacts/templates",
    "references/roadmap/SHA256SUMS",
)

EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


def _iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        return []
    return sorted(
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file()
        and not any(part in EXCLUDED_DIR_NAMES for part in candidate.parts)
    )


def _git_commit() -> str:
    try:
        result = subprocess.run(  # noqa: S603,S607 - fixed argv, no shell
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip() or "UNKNOWN"
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - defensive
        return "UNKNOWN"


def build_bundle(output_root: Path, include_tevv: bool) -> dict[str, Any]:
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = output_root / f"evidence_bundle_{stamp}"
    files_dir = bundle_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    corpus = load_corpus_fixtures()
    entries: list[dict[str, Any]] = []

    for tracked in TRACKED_PATHS:
        source_path = REPO_ROOT / tracked
        for file_path in _iter_files(source_path):
            relative = file_path.relative_to(REPO_ROOT)
            destination = files_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, destination)
            entries.append(
                {
                    "path": str(relative),
                    "sha256": file_sha256(str(file_path)),
                    "bytes": file_path.stat().st_size,
                    "category": tracked.split("/")[0],
                }
            )

    if include_tevv:
        tevv_dir = get_settings().artifacts_dir / "tevv"
        for file_path in _iter_files(tevv_dir):
            relative = Path("artifacts/tevv") / file_path.name
            destination = files_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, destination)
            entries.append(
                {
                    "path": str(relative),
                    "sha256": file_sha256(str(file_path)),
                    "bytes": file_path.stat().st_size,
                    "category": "tevv",
                }
            )

    manifest: dict[str, Any] = {
        "bundle_id": f"evidence_bundle_{stamp}",
        "generated_at": utc_now().isoformat().replace("+00:00", "Z"),
        "environment_id": ENVIRONMENT_ID,
        "git_commit": _git_commit(),
        "component_versions": dict(COMPONENT_VERSIONS),
        "corpus_manifest_sha256": corpus.manifest_sha256,
        "rule_catalog": catalog_payload(),
        "artifact_count": len(entries),
        "artifacts": sorted(entries, key=lambda entry: str(entry["path"])),
        "status_dimensions": {
            "built": "NOT_EVIDENCED",
            "integration": "NOT_EVIDENCED",
            "operational": "NOT_EVIDENCED",
            "authorization": "NOT_GRANTED",
        },
        "acceptance_state": "NOT_ACCEPTED",
        "notice": (
            "This bundle inventories artifacts produced by the implementation team. It is "
            "candidate developer-verification evidence only. Independent code review, "
            "independent security testing, independent TEVV, deployment validation and "
            "human-owner acceptance are separate, ordered gates that this bundle does not "
            "satisfy and cannot self-certify."
        ),
        "three_function_separation": {
            "technical_owner": "prepares code and developer evidence",
            "independent_evaluator": "reviews code, security, TEVV and deployment results",
            "human_owner": "accepts or rejects a narrow evidence or status claim",
            "rule": (
                "One identity must not perform all three functions for the same component, "
                "version, status dimension and evidence set."
            ),
        },
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)

    manifest_path = bundle_dir / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    checksums = bundle_dir / "SHA256SUMS"
    checksums.write_text(
        "".join(
            f"{entry['sha256']}  files/{entry['path']}\n"
            for entry in manifest["artifacts"]
        ),
        encoding="utf-8",
    )

    readme = bundle_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# Evidence bundle {manifest['bundle_id']}",
                "",
                f"- Environment: `{ENVIRONMENT_ID}`",
                f"- Generated at: {manifest['generated_at']}",
                f"- Git commit: `{manifest['git_commit']}`",
                f"- Corpus manifest SHA-256: `{manifest['corpus_manifest_sha256']}`",
                f"- Artifacts: {manifest['artifact_count']}",
                f"- Manifest SHA-256: `{manifest['manifest_sha256']}`",
                "",
                "## Status dimensions",
                "",
                "| Dimension | Value |",
                "|---|---|",
                "| Built | NOT_EVIDENCED |",
                "| Integration | NOT_EVIDENCED |",
                "| Operational | NOT_EVIDENCED |",
                "| Authorization | NOT_GRANTED |",
                "",
                "## What this bundle is not",
                "",
                str(manifest["notice"]),
                "",
                "## Verifying",
                "",
                "```bash",
                "cd <bundle directory>",
                "sha256sum -c SHA256SUMS",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"bundle_dir": bundle_dir, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--include-tevv", action="store_true", default=True)
    parser.add_argument("--no-include-tevv", dest="include_tevv", action="store_false")
    args = parser.parse_args()

    output_root = args.output or get_settings().artifacts_dir
    output_root.mkdir(parents=True, exist_ok=True)
    result = build_bundle(output_root, args.include_tevv)
    manifest = result["manifest"]
    bundle_dir = result["bundle_dir"]

    print(f"bundle directory : {bundle_dir}")
    print(f"artifacts        : {manifest['artifact_count']}")
    print(f"manifest sha256  : {manifest['manifest_sha256']}")
    print(f"git commit       : {manifest['git_commit']}")
    print()
    print(
        "Built: NOT_EVIDENCED | Integration: NOT_EVIDENCED | "
        "Operational: NOT_EVIDENCED | Authorization: NOT_GRANTED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
