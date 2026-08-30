#!/usr/bin/env python3
"""Seed the frozen synthetic corpus and control-plane fixtures.

Seeding is the only path by which source content enters the database. There is no runtime
upload, no dynamic ingestion and no repository mutation from the running service.

The seed fails closed if any source file hash does not match ``manifest.json``, or if the
manifest self-hash does not match its own content.

PyMuPDF is used here, during seeding only, to render a derived read-only PDF facsimile of
each source and to cross-check its page count against the parsed structure. The facsimile
is a convenience artifact; the authored text file remains the hashed source of truth.

Usage:
    python scripts/seed_synthetic_corpus.py [--reset] [--no-pdf]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from sqlalchemy import delete, select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.domain.canonical import file_sha256, utc_now  # noqa: E402
from app.repositories.database import session_scope  # noqa: E402
from app.repositories.tables import (  # noqa: E402
    AuthorizationDecisionRow,
    DemoIdentityRow,
    DemoSessionRow,
    ModelConfigurationRow,
    SourceBlockRow,
    SourcePageRow,
    SourceRecordRow,
    SourceVersionRow,
    UseCaseContractRow,
)
from app.services.corpus import parse_source_file  # noqa: E402
from app.services.fixtures import (  # noqa: E402
    load_authorizations,
    load_corpus_fixtures,
    load_identities,
    load_model_configurations,
    load_use_case_contract,
    source_file_path,
)


class SeedError(RuntimeError):
    pass


def _parse_iso(value: str | None):  # type: ignore[no-untyped-def]
    from datetime import datetime

    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def render_pdf_facsimile(text: str, destination: Path) -> int:
    """Render a derived read-only PDF and return its page count. Seeding only."""
    import fitz  # PyMuPDF

    document = fitz.open()
    for page_text in text.split("<<<PAGE ")[1:]:
        body = page_text.split(">>>", 1)[1] if ">>>" in page_text else page_text
        page = document.new_page()
        page.insert_textbox(
            fitz.Rect(56, 56, 539, 785), body.strip(), fontsize=9, fontname="helv", align=0
        )
    document.set_metadata({"title": destination.stem, "producer": "nabd-seed", "creationDate": ""})
    destination.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(destination), deflate=True)
    page_count = document.page_count
    document.close()
    return page_count


def seed(*, reset: bool, render_pdf: bool) -> int:
    settings = get_settings()
    corpus = load_corpus_fixtures()
    identities = load_identities()
    authorizations = load_authorizations()
    contract = load_use_case_contract()
    configurations = load_model_configurations()

    print(f"corpus manifest sha256 : {corpus.manifest_sha256}")
    print(f"database               : {'sqlite' if settings.is_sqlite else 'postgresql'}")

    for item in corpus.sources:
        path = source_file_path(item)
        if not path.exists():
            raise SeedError(f"source file listed in the manifest is missing: {path}")
        actual = file_sha256(str(path))
        if actual != item.source_sha256:
            raise SeedError(
                f"hash mismatch for {item.source_key}: manifest={item.source_sha256} actual={actual}"
            )

    with session_scope() as session:
        if reset:
            # Deletion order follows the foreign keys: dependants first, so a reset never
            # trips a constraint on a database that already holds demo sessions.
            for table in (
                DemoSessionRow,
                SourceBlockRow,
                SourcePageRow,
                SourceVersionRow,
                SourceRecordRow,
                DemoIdentityRow,
                AuthorizationDecisionRow,
                UseCaseContractRow,
                ModelConfigurationRow,
            ):
                session.execute(delete(table))
            session.flush()

        for identity in identities.values():
            if session.get(DemoIdentityRow, identity.identity_id) is None:
                session.add(
                    DemoIdentityRow(
                        identity_id=identity.identity_id,
                        role=identity.role.value,
                        role_id=identity.role_id,
                        business_scope_id=identity.business_scope_id,
                        status=identity.status.value,
                        selectable_in_ui=identity.selectable_in_ui,
                        payload=identity.model_dump(mode="json"),
                    )
                )

        for authorization in authorizations.values():
            if session.get(AuthorizationDecisionRow, authorization.authorization_id) is None:
                session.add(
                    AuthorizationDecisionRow(
                        authorization_id=authorization.authorization_id,
                        environment_id=authorization.environment_id,
                        use_case_contract_id=authorization.use_case_contract_id,
                        source_manifest_sha256=authorization.source_manifest_sha256,
                        demo_period_start=authorization.demo_period_start,
                        demo_period_end=authorization.demo_period_end,
                        revoked=authorization.revoked,
                        payload=authorization.model_dump(mode="json"),
                    )
                )

        if session.get(UseCaseContractRow, contract.use_case_contract_id) is None:
            session.add(
                UseCaseContractRow(
                    use_case_contract_id=contract.use_case_contract_id,
                    business_scope_id=contract.business_scope_id,
                    payload=contract.model_dump(mode="json"),
                )
            )

        for configuration in configurations.values():
            if session.get(ModelConfigurationRow, configuration.model_configuration_id) is None:
                session.add(
                    ModelConfigurationRow(
                        model_configuration_id=configuration.model_configuration_id,
                        task_role=configuration.task_role.value,
                        model_revision=configuration.model_revision,
                        prompt_version=configuration.prompt_version,
                        mode=configuration.mode.value,
                        revoked=configuration.revoked,
                        payload=configuration.model_dump(mode="json"),
                    )
                )
        session.flush()

        seen_source_ids: set[str] = set()
        block_total = 0
        for item in corpus.sources:
            path = source_file_path(item)
            document = parse_source_file(path)
            if document.extracted_text_sha256 != item.extracted_text_sha256:
                raise SeedError(f"extracted text hash drifted for {item.source_key}")
            if len(document.pages) != item.page_count:
                raise SeedError(f"page count drifted for {item.source_key}")

            if item.source_id not in seen_source_ids:
                if session.get(SourceRecordRow, item.source_id) is None:
                    session.add(
                        SourceRecordRow(
                            source_id=item.source_id,
                            title=item.title,
                            owner=item.owner,
                            authority_class=item.authority_class.value,
                            business_scope_id=item.business_scope_id,
                        )
                    )
                seen_source_ids.add(item.source_id)
                session.flush()

            if session.get(SourceVersionRow, item.source_key) is None:
                session.add(
                    SourceVersionRow(
                        source_version_key=item.source_key,
                        source_id=item.source_id,
                        source_version=item.source_version,
                        lifecycle=item.lifecycle.value,
                        effective_from=_parse_iso(item.effective_from),
                        effective_to=_parse_iso(item.effective_to),
                        revoked_at=_parse_iso(item.revoked_at),
                        superseded_by=item.superseded_by,
                        quarantine_reason=item.quarantine_reason,
                        business_scope_id=item.business_scope_id,
                        access_labels=list(item.access_labels),
                        permitted_use_case_ids=list(item.permitted_use_case_ids),
                        source_path=item.source_path,
                        source_sha256=item.source_sha256,
                        extracted_text_sha256=item.extracted_text_sha256,
                        instruction_like_flags={
                            "body": list(item.body_instruction_flags),
                            "metadata": list(item.metadata_instruction_flags),
                        },
                        payload={
                            "title": item.title,
                            "owner": item.owner,
                            "authority_class": item.authority_class.value,
                            "eligibility_purpose": item.eligibility_purpose,
                            "topics": list(item.topics),
                            "revocation_reason": item.revocation_reason,
                            "seeded_at": utc_now().isoformat(),
                        },
                    )
                )
                session.flush()

            for page in document.pages:
                page_id = f"{item.source_key}#p{page.page_number}"
                if session.get(SourcePageRow, page_id) is None:
                    session.add(
                        SourcePageRow(
                            source_page_id=page_id,
                            source_version_key=item.source_key,
                            page_number=page.page_number,
                            section_headings=list(page.section_headings),
                            char_start=page.char_start,
                            char_end=page.char_end,
                            block_count=page.block_count,
                            page_text=document.raw_text[page.char_start : page.char_end],
                        )
                    )
            session.flush()

            for block in document.blocks:
                block_id = f"{item.source_key}#b{block.block_index:03d}"
                if session.get(SourceBlockRow, block_id) is None:
                    session.add(
                        SourceBlockRow(
                            source_block_id=block_id,
                            source_page_id=f"{item.source_key}#p{block.page_number}",
                            source_version_key=item.source_key,
                            block_index=block.block_index,
                            page_number=block.page_number,
                            section_heading=block.section_heading,
                            char_start=block.char_start,
                            char_end=block.char_end,
                            text=block.text,
                            text_sha256=block.text_sha256,
                            instruction_like_flags=list(block.instruction_like_flags),
                        )
                    )
                    block_total += 1
            session.flush()

            if render_pdf:
                destination = settings.artifacts_dir / "derived_pdf" / f"{item.source_key}.pdf"
                pages = render_pdf_facsimile(document.raw_text, destination)
                if pages != len(document.pages):
                    raise SeedError(
                        f"derived PDF page count ({pages}) disagrees with the parsed structure "
                        f"({len(document.pages)}) for {item.source_key}"
                    )

        version_count = len(session.execute(select(SourceVersionRow)).scalars().all())
        block_count = len(session.execute(select(SourceBlockRow)).scalars().all())

    print(f"identities             : {len(identities)}")
    print(f"authorization fixtures : {len(authorizations)}")
    print(f"model configurations   : {len(configurations)}")
    print(f"source versions        : {version_count}")
    print(f"retrievable blocks     : {block_count} (new this run: {block_total})")
    print("seed complete: every source file hash matched the frozen manifest")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="delete existing corpus rows first")
    parser.add_argument("--no-pdf", action="store_true", help="skip the derived PDF facsimile")
    args = parser.parse_args()
    try:
        return seed(reset=args.reset, render_pdf=not args.no_pdf)
    except SeedError as error:
        print(f"seed failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
