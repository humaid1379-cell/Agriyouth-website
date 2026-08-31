"""Source eligibility.

Eligibility is decided before ranking and before any model call (INV-04). A source that
fails any check is excluded with a reason code; it can never be reintroduced later by a
ranking score, a model citation or a reviewer preference.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.canonical import file_sha256
from app.domain.enums import SourceLifecycle
from app.domain.reason_codes import ReasonCode
from app.services.fixtures import (
    CorpusFixtures,
    SourceManifestItem,
    load_corpus_fixtures,
    source_file_path,
)


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    item: SourceManifestItem
    eligible: bool
    reason_code: str
    detail: str

    @property
    def source_key(self) -> str:
        return self.item.source_key


@dataclass(frozen=True, slots=True)
class EligibilityReport:
    decisions: tuple[EligibilityDecision, ...]
    hash_mismatches: tuple[str, ...]

    @property
    def eligible(self) -> tuple[SourceManifestItem, ...]:
        return tuple(d.item for d in self.decisions if d.eligible)

    @property
    def excluded(self) -> tuple[tuple[str, ReasonCode], ...]:
        return tuple(
            (d.source_key, ReasonCode(d.reason_code))
            for d in self.decisions
            if not d.eligible and d.reason_code in ReasonCode.__members__.values()
        )

    @property
    def excluded_keys(self) -> tuple[str, ...]:
        return tuple(d.source_key for d in self.decisions if not d.eligible)

    @property
    def quarantined(self) -> tuple[str, ...]:
        return tuple(
            d.source_key
            for d in self.decisions
            if not d.eligible and d.reason_code == ReasonCode.SOURCE_QUARANTINED.value
        )


def evaluate_source_eligibility(
    *,
    at: datetime,
    business_scope_id: str,
    use_case_contract_id: str,
    access_labels: frozenset[str],
    verify_file_hashes: bool = True,
    fixtures: CorpusFixtures | None = None,
) -> EligibilityReport:
    """Apply manifest, lifecycle, scope, use-case, access and hash filters."""
    corpus = fixtures or load_corpus_fixtures()
    decisions: list[EligibilityDecision] = []
    mismatches: list[str] = []

    for item in corpus.sources:
        if verify_file_hashes:
            path = source_file_path(item)
            actual = file_sha256(str(path)) if path.exists() else ""
            if actual != item.source_sha256:
                mismatches.append(item.source_key)
                decisions.append(
                    EligibilityDecision(
                        item,
                        False,
                        ReasonCode.MANIFEST_HASH_MISMATCH.value,
                        "Source file hash does not match the frozen manifest.",
                    )
                )
                continue

        if item.is_quarantined:
            decisions.append(
                EligibilityDecision(
                    item,
                    False,
                    ReasonCode.SOURCE_QUARANTINED.value,
                    item.quarantine_reason or "Instruction-like content detected.",
                )
            )
            continue

        if item.lifecycle is not SourceLifecycle.ACTIVE:
            decisions.append(
                EligibilityDecision(
                    item,
                    False,
                    ReasonCode.SOURCE_ELIGIBILITY_FAILURE.value,
                    f"Lifecycle is {item.lifecycle.value}, not ACTIVE.",
                )
            )
            continue

        if item.business_scope_id != business_scope_id:
            decisions.append(
                EligibilityDecision(
                    item,
                    False,
                    ReasonCode.ACCESS_DENIED.value,
                    "Source belongs to another business unit scope.",
                )
            )
            continue

        if use_case_contract_id not in item.permitted_use_case_ids:
            decisions.append(
                EligibilityDecision(
                    item,
                    False,
                    ReasonCode.SOURCE_ELIGIBILITY_FAILURE.value,
                    "Source is not permitted for this use case contract.",
                )
            )
            continue

        if access_labels and not set(item.access_labels) & access_labels:
            decisions.append(
                EligibilityDecision(
                    item,
                    False,
                    ReasonCode.ACCESS_DENIED.value,
                    "No access label of this identity matches the source.",
                )
            )
            continue

        effective_from = datetime.fromisoformat(item.effective_from.replace("Z", "+00:00"))
        if at < effective_from:
            decisions.append(
                EligibilityDecision(
                    item,
                    False,
                    ReasonCode.SOURCE_ELIGIBILITY_FAILURE.value,
                    "Source is not yet effective.",
                )
            )
            continue
        if item.effective_to:
            effective_to = datetime.fromisoformat(item.effective_to.replace("Z", "+00:00"))
            if at > effective_to:
                decisions.append(
                    EligibilityDecision(
                        item,
                        False,
                        ReasonCode.SOURCE_ELIGIBILITY_FAILURE.value,
                        "Source effective period has ended.",
                    )
                )
                continue

        decisions.append(
            EligibilityDecision(item, True, "OK", "Eligible under the frozen manifest.")
        )

    return EligibilityReport(decisions=tuple(decisions), hash_mismatches=tuple(mismatches))
