"""Loader for build-controlled control-plane fixtures.

Everything here is read-only repository data validated against closed schemas at load
time. There is no code path that writes an authorization, a use-case contract, a source
manifest entry, an identity or a model configuration at runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from app.config import REPO_ROOT, get_settings
from app.domain.canonical import canonical_sha256, file_sha256
from app.domain.enums import AuthorityClass, ModelTaskRole, SourceLifecycle
from app.domain.versions import CORPUS_VERSION
from app.schemas.evidence import ManifestEntry
from app.schemas.governance import AuthorizationDecision, DemoIdentity, UseCaseContract
from app.schemas.model_io import ModelConfiguration

FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"


class FixtureError(RuntimeError):
    """A control-plane fixture is missing, malformed or internally inconsistent."""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FixtureError(f"required fixture file is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise FixtureError(f"fixture file is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise FixtureError(f"fixture file must contain a JSON object: {path}")
    return payload


@dataclass(frozen=True, slots=True)
class SourceManifestItem:
    """One frozen source-version entry, with eligibility metadata and integrity hashes."""

    source_id: str
    source_version: str
    source_key: str
    title: str
    owner: str
    authority_class: AuthorityClass
    lifecycle: SourceLifecycle
    effective_from: str
    effective_to: str | None
    business_scope_id: str
    permitted_use_case_ids: tuple[str, ...]
    access_labels: tuple[str, ...]
    supersedes: str | None
    superseded_by: str | None
    revoked_at: str | None
    revocation_reason: str | None
    quarantine_reason: str | None
    quarantine_metadata_probe: str | None
    eligibility_purpose: str
    topics: tuple[str, ...]
    source_path: str
    source_sha256: str
    extracted_text_sha256: str
    page_count: int
    block_count: int
    body_instruction_flags: tuple[str, ...]
    metadata_instruction_flags: tuple[str, ...]
    active: bool

    @property
    def is_quarantined(self) -> bool:
        return self.lifecycle is SourceLifecycle.QUARANTINED or bool(
            self.body_instruction_flags or self.metadata_instruction_flags
        )

    def to_manifest_entry(self) -> ManifestEntry:
        return ManifestEntry(
            source_id=self.source_id,
            source_version=self.source_version,
            source_path=self.source_path,
            source_sha256=self.source_sha256,
            lifecycle=self.lifecycle,
            active=self.active,
        )


@dataclass(frozen=True, slots=True)
class ConflictDeclaration:
    conflict_id: str
    topic: str
    materiality: str
    description_en: str
    description_ar: str
    trigger_all_terms: tuple[str, ...]
    trigger_any_terms: tuple[str, ...]
    party_a_source_key: str
    party_b_source_key: str
    required_resolution: str
    expected_reason_code: str

    def question_triggers(self, normalised_question: str) -> bool:
        text = normalised_question.casefold()
        if not all(term.casefold() in text for term in self.trigger_all_terms):
            return False
        if not self.trigger_any_terms:
            return True
        return any(term.casefold() in text for term in self.trigger_any_terms)


@dataclass(frozen=True, slots=True)
class RevocationDeclaration:
    revocation_id: str
    source_key: str
    lifecycle: str
    revoked_at: str
    reason_en: str
    reason_ar: str
    historical_warning_en: str
    future_use_blocked: bool


@dataclass(frozen=True, slots=True)
class CorpusFixtures:
    manifest: dict[str, Any]
    manifest_sha256: str
    manifest_file_sha256: str
    sources: tuple[SourceManifestItem, ...]
    conflicts: tuple[ConflictDeclaration, ...]
    revocations: tuple[RevocationDeclaration, ...]

    def by_key(self, source_key: str) -> SourceManifestItem | None:
        for item in self.sources:
            if item.source_key == source_key:
                return item
        return None

    def by_source_id(self, source_id: str) -> tuple[SourceManifestItem, ...]:
        return tuple(item for item in self.sources if item.source_id == source_id)

    def revocation_for(self, source_key: str) -> RevocationDeclaration | None:
        for revocation in self.revocations:
            if revocation.source_key == source_key:
                return revocation
        return None


def _corpus_dir() -> Path:
    return get_settings().corpus_dir


@lru_cache(maxsize=1)
def load_corpus_fixtures() -> CorpusFixtures:
    corpus_dir = _corpus_dir()
    manifest_path = corpus_dir / "manifest.json"
    manifest = _read_json(manifest_path)

    recorded = manifest.get("manifest_sha256")
    preimage = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    recomputed = canonical_sha256(preimage)
    if recorded != recomputed:
        raise FixtureError(
            "manifest.json self-hash does not match its content "
            f"(recorded={recorded!r}, recomputed={recomputed!r})"
        )
    if manifest.get("corpus_id") != CORPUS_VERSION:
        raise FixtureError("manifest corpus_id does not match the pinned corpus version")

    sources: list[SourceManifestItem] = []
    for entry in manifest.get("sources", []):
        flags = entry.get("instruction_like_flags", {})
        sources.append(
            SourceManifestItem(
                source_id=entry["source_id"],
                source_version=entry["source_version"],
                source_key=entry["source_key"],
                title=entry["title"],
                owner=entry["owner"],
                authority_class=AuthorityClass(entry["authority_class"]),
                lifecycle=SourceLifecycle(entry["lifecycle"]),
                effective_from=entry["effective_from"],
                effective_to=entry.get("effective_to"),
                business_scope_id=entry["business_scope_id"],
                permitted_use_case_ids=tuple(entry.get("permitted_use_case_ids", ())),
                access_labels=tuple(entry.get("access_labels", ())),
                supersedes=entry.get("supersedes"),
                superseded_by=entry.get("superseded_by"),
                revoked_at=entry.get("revoked_at"),
                revocation_reason=entry.get("revocation_reason"),
                quarantine_reason=entry.get("quarantine_reason"),
                quarantine_metadata_probe=entry.get("quarantine_metadata_probe"),
                eligibility_purpose=entry["eligibility_purpose"],
                topics=tuple(entry.get("topics", ())),
                source_path=entry["source_path"],
                source_sha256=entry["source_sha256"],
                extracted_text_sha256=entry["extracted_text_sha256"],
                page_count=int(entry["page_count"]),
                block_count=int(entry["block_count"]),
                body_instruction_flags=tuple(flags.get("body", ())),
                metadata_instruction_flags=tuple(flags.get("metadata", ())),
                active=bool(entry["active"]),
            )
        )

    conflicts_payload = _read_json(corpus_dir / "conflicts.json")
    conflicts = tuple(
        ConflictDeclaration(
            conflict_id=item["conflict_id"],
            topic=item["topic"],
            materiality=item["materiality"],
            description_en=item["description_en"],
            description_ar=item.get("description_ar", ""),
            trigger_all_terms=tuple(item.get("trigger_all_terms", ())),
            trigger_any_terms=tuple(item.get("trigger_any_terms", ())),
            party_a_source_key=item["party_a"]["source_key"],
            party_b_source_key=item["party_b"]["source_key"],
            required_resolution=item["required_resolution"],
            expected_reason_code=item["expected_reason_code"],
        )
        for item in conflicts_payload.get("conflicts", [])
    )

    revocations_payload = _read_json(corpus_dir / "revocations.json")
    revocations = tuple(
        RevocationDeclaration(
            revocation_id=item["revocation_id"],
            source_key=item["source_key"],
            lifecycle=item["lifecycle"],
            revoked_at=item["revoked_at"],
            reason_en=item["reason_en"],
            reason_ar=item.get("reason_ar", ""),
            historical_warning_en=item.get("historical_warning_en", ""),
            future_use_blocked=bool(item.get("future_use_blocked", True)),
        )
        for item in revocations_payload.get("revocations", [])
    )

    return CorpusFixtures(
        manifest=manifest,
        manifest_sha256=str(recorded),
        manifest_file_sha256=file_sha256(str(manifest_path)),
        sources=tuple(sources),
        conflicts=conflicts,
        revocations=revocations,
    )


_AUTH_ADAPTER = TypeAdapter(AuthorizationDecision)
_CONTRACT_ADAPTER = TypeAdapter(UseCaseContract)
_IDENTITY_ADAPTER = TypeAdapter(DemoIdentity)
_MODEL_ADAPTER = TypeAdapter(ModelConfiguration)


@lru_cache(maxsize=1)
def load_authorizations() -> dict[str, AuthorizationDecision]:
    payload = _read_json(FIXTURES_DIR / "authorization.json")
    return {
        str(item["authorization_id"]): _AUTH_ADAPTER.validate_python(item)
        for item in payload.get("authorizations", [])
    }


@lru_cache(maxsize=1)
def primary_authorization() -> AuthorizationDecision:
    payload = _read_json(FIXTURES_DIR / "authorization.json")
    primary_id = str(payload["primary_authorization_id"])
    authorizations = load_authorizations()
    if primary_id not in authorizations:
        raise FixtureError(f"primary authorization {primary_id} is not defined")
    return authorizations[primary_id]


@lru_cache(maxsize=1)
def load_use_case_contract() -> UseCaseContract:
    payload = _read_json(FIXTURES_DIR / "use_case_contract.json")
    contracts = payload.get("contracts", [])
    if not contracts:
        raise FixtureError("no use case contract is defined")
    known_extra = {
        "supporting_source_authority_classes",
        "multi_question_markers",
        "min_question_chars",
    }
    raw = dict(contracts[0])
    extras = {key: raw.pop(key) for key in list(raw) if key in known_extra}
    contract = _CONTRACT_ADAPTER.validate_python(raw)
    _CONTRACT_EXTRAS.clear()
    _CONTRACT_EXTRAS.update(extras)
    return contract


#: Auxiliary contract data that is deliberately not part of the closed contract schema.
_CONTRACT_EXTRAS: dict[str, Any] = {}


def contract_extras() -> dict[str, Any]:
    if not _CONTRACT_EXTRAS:
        load_use_case_contract()
    return dict(_CONTRACT_EXTRAS)


@lru_cache(maxsize=1)
def load_identities() -> dict[str, DemoIdentity]:
    payload = _read_json(FIXTURES_DIR / "identities.json")
    return {
        str(item["identity_id"]): _IDENTITY_ADAPTER.validate_python(item)
        for item in payload.get("identities", [])
    }


@lru_cache(maxsize=1)
def load_model_configurations() -> dict[str, ModelConfiguration]:
    payload = _read_json(FIXTURES_DIR / "model_configurations.json")
    return {
        str(item["model_configuration_id"]): _MODEL_ADAPTER.validate_python(item)
        for item in payload.get("configurations", [])
    }


@lru_cache(maxsize=1)
def active_model_configuration_ids() -> dict[ModelTaskRole, str]:
    payload = _read_json(FIXTURES_DIR / "model_configurations.json")
    return {
        ModelTaskRole.DRAFTER: str(payload["active_draft_configuration_id"]),
        ModelTaskRole.VERIFIER: str(payload["active_verifier_configuration_id"]),
    }


def active_model_configuration(task_role: ModelTaskRole) -> ModelConfiguration:
    configuration_id = active_model_configuration_ids()[task_role]
    configurations = load_model_configurations()
    if configuration_id not in configurations:
        raise FixtureError(f"active model configuration {configuration_id} is not defined")
    return configurations[configuration_id]


def source_file_path(item: SourceManifestItem) -> Path:
    return _corpus_dir() / item.source_path


def reset_fixture_cache() -> None:
    """Used by tests that point the loader at a temporary corpus."""
    for cached in (
        load_corpus_fixtures,
        load_authorizations,
        primary_authorization,
        load_use_case_contract,
        load_identities,
        load_model_configurations,
        active_model_configuration_ids,
    ):
        cached.cache_clear()
    _CONTRACT_EXTRAS.clear()
