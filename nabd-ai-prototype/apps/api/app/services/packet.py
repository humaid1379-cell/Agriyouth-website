"""Decision Readiness Packet assembly, sealing and semantic validation.

JSON Schema validation alone is not enough: a packet can be structurally perfect and still
reference the wrong case, cite an ineligible source, or claim a route it did not earn.
:func:`validate_packet_semantics` implements the eleven semantic invariants of Section 12.1
as explicit, individually reportable checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.canonical import compute_packet_hash, utc_now, verify_packet_hash
from app.domain.enums import (
    Materiality,
    RiskLevel,
    Route,
    SupportState,
)
from app.domain.notices import NOTICE_TEXT_BY_ID, REQUIRED_NOTICE_IDS, notices_payload
from app.domain.versions import (
    AUDIT_CHAIN_VERSION,
    CORPUS_VERSION,
    PACKET_SCHEMA_VERSION,
    PROMPT_DRAFT_VERSION,
    PROMPT_VERIFY_VERSION,
    RETRIEVAL_VERSION,
    RULE_CATALOG_VERSION,
    SCHEMA_VERSION,
    WORKFLOW_VERSION,
)
from app.schemas.evidence import EvidenceExcerpt
from app.schemas.governance import AuthorizationDecision
from app.schemas.packet import (
    DecisionReadinessPacket,
    PacketAuditBinding,
    PacketAuthorizationContext,
    PacketEvidenceManifestItem,
    PacketIdentity,
    PacketIntegrity,
    PacketNotice,
    PacketRequestContext,
    PacketStatusBlock,
    PacketVersionLineage,
)
from app.schemas.reasoning import (
    DeterministicResult,
    GeneratedClaim,
    RiskProfile,
    UncertaintyRecord,
)
from app.services.fixtures import SourceManifestItem

PACKET_SERVICE_ID = "service:packet-assembly"

#: Terms that must never appear in a packet. A packet is a decision-support artifact.
PROHIBITED_PACKET_TERMS: tuple[str, ...] = (
    "webhook",
    "http://",
    "https://",
    "action_id",
    "execute_action",
    "approve_action",
    "send_email",
    "payment",
)

STANDARD_LIMITATIONS: tuple[str, ...] = (
    "Claims are limited to the admitted synthetic excerpts recorded in this packet.",
    "The corpus is a frozen synthetic collection; it does not reflect any real institution.",
    "The prototype supports and prepares a decision. It does not make or execute one.",
    "This packet demonstrates no production, operational or institutional authorization.",
)


@dataclass(frozen=True, slots=True)
class PacketInputs:
    case_id: str
    packet_id: str
    packet_version: int
    authorization: AuthorizationDecision
    requester_identity_id: str
    requester_role: Any
    submitted_at: datetime
    normalised_question: str
    question_sha256: str
    permitted_purpose: str
    excerpts: tuple[EvidenceExcerpt, ...]
    source_items: tuple[SourceManifestItem, ...]
    claims: tuple[GeneratedClaim, ...]
    rule_results: tuple[DeterministicResult, ...]
    uncertainty: tuple[UncertaintyRecord, ...]
    conflicts: tuple[str, ...]
    risk: RiskProfile
    route: Route
    route_reason_code: str
    draft_configuration_id: str
    verifier_configuration_id: str
    created_at: datetime
    pre_issuance_event_id: str | None = None
    audit_chain_head_hash: str | None = None


def build_packet(inputs: PacketInputs) -> DecisionReadinessPacket:
    """Assemble a packet and seal it with the canonical SHA-256."""
    authority_by_key = {item.source_key: item.authority_class.value for item in inputs.source_items}

    manifest_items = tuple(
        PacketEvidenceManifestItem(
            excerpt_id=excerpt.excerpt_id,
            source_id=excerpt.source_id,
            source_version=excerpt.source_version,
            authority_class=authority_by_key.get(
                f"{excerpt.source_id}@{excerpt.source_version}", "UNKNOWN"
            ),
            page_number=excerpt.page_number,
            section_heading=excerpt.section_heading,
            char_start=excerpt.char_start,
            char_end=excerpt.char_end,
            excerpt_sha256=excerpt.text_sha256,
            source_sha256=excerpt.source_sha256,
            retrieved_at=excerpt.created_at,
        )
        for excerpt in sorted(inputs.excerpts, key=lambda e: e.excerpt_id)
    )

    packet = DecisionReadinessPacket(
        identity=PacketIdentity(
            packet_id=inputs.packet_id,
            packet_version=inputs.packet_version,
            case_id=inputs.case_id,
            created_at=inputs.created_at,
        ),
        authorization_context=PacketAuthorizationContext(
            authorization_id=inputs.authorization.authorization_id,
            fixture_notice=inputs.authorization.fixture_notice,
            use_case_contract_id=inputs.authorization.use_case_contract_id,
            demo_period_start=inputs.authorization.demo_period_start,
            demo_period_end=inputs.authorization.demo_period_end,
            source_manifest_sha256=inputs.authorization.source_manifest_sha256,
        ),
        request_context=PacketRequestContext(
            requester_identity_id=inputs.requester_identity_id,
            requester_role=inputs.requester_role,
            submitted_at=inputs.submitted_at,
            normalised_question=inputs.normalised_question,
            permitted_purpose=inputs.permitted_purpose,
            question_sha256=inputs.question_sha256,
        ),
        evidence_manifest=manifest_items,
        claim_ledger=tuple(sorted(inputs.claims, key=lambda c: c.claim_ref)),
        rule_results=tuple(
            sorted(
                inputs.rule_results, key=lambda r: (r.precedence_rank, r.rule_id, r.evaluated_at)
            )
        ),
        uncertainty=inputs.uncertainty,
        conflicts=inputs.conflicts,
        risk=inputs.risk,
        limitations=STANDARD_LIMITATIONS,
        route=inputs.route,
        route_reason_code=inputs.route_reason_code,
        version_lineage=PacketVersionLineage(
            workflow_version=WORKFLOW_VERSION,
            schema_version=SCHEMA_VERSION,
            rule_catalog_version=RULE_CATALOG_VERSION,
            corpus_version=CORPUS_VERSION,
            retrieval_version=RETRIEVAL_VERSION,
            prompt_draft_version=PROMPT_DRAFT_VERSION,
            prompt_verify_version=PROMPT_VERIFY_VERSION,
            packet_schema_version=PACKET_SCHEMA_VERSION,
            audit_chain_version=AUDIT_CHAIN_VERSION,
            draft_model_configuration_id=inputs.draft_configuration_id,
            verifier_model_configuration_id=inputs.verifier_configuration_id,
        ),
        integrity=PacketIntegrity(calculated_at=inputs.created_at),
        audit_binding=PacketAuditBinding(
            pre_issuance_event_id=inputs.pre_issuance_event_id,
            audit_chain_head_hash=inputs.audit_chain_head_hash,
        ),
        notices=tuple(PacketNotice(**notice) for notice in notices_payload()),
        prototype_status=PacketStatusBlock(),
    )
    return seal(packet)


def seal(packet: DecisionReadinessPacket) -> DecisionReadinessPacket:
    """Recompute and attach the canonical packet hash."""
    payload = packet.model_dump(mode="json")
    digest = compute_packet_hash(payload)
    return packet.model_copy(
        update={
            "integrity": packet.integrity.model_copy(
                update={"packet_sha256": digest, "calculated_at": packet.integrity.calculated_at}
            )
        }
    )


def with_audit_binding(
    packet: DecisionReadinessPacket,
    *,
    pre_issuance_event_id: str | None = None,
    pre_issuance_confirmed_at: datetime | None = None,
    closure_event_id: str | None = None,
    closure_confirmed_at: datetime | None = None,
    chain_head_hash: str | None = None,
) -> DecisionReadinessPacket:
    """Bind confirmed audit references, then reseal.

    The audit binding is part of the sealed preimage, so a packet displayed without its
    confirmed pre-issuance event would not match its own recorded hash.
    """
    binding = packet.audit_binding.model_copy(
        update={
            "pre_issuance_event_id": pre_issuance_event_id
            or packet.audit_binding.pre_issuance_event_id,
            "pre_issuance_confirmed_at": pre_issuance_confirmed_at
            or packet.audit_binding.pre_issuance_confirmed_at,
            "disposition_closure_event_id": closure_event_id
            or packet.audit_binding.disposition_closure_event_id,
            "disposition_closure_confirmed_at": closure_confirmed_at
            or packet.audit_binding.disposition_closure_confirmed_at,
            "audit_chain_head_hash": chain_head_hash or packet.audit_binding.audit_chain_head_hash,
        }
    )
    return seal(packet.model_copy(update={"audit_binding": binding}))


@dataclass(frozen=True, slots=True)
class SemanticContext:
    """Facts the validator checks the packet against, gathered independently of it."""

    case_id: str
    authorization: AuthorizationDecision
    eligible_source_keys: frozenset[str]
    admitted_excerpt_ids: frozenset[str]
    #: The hash sealed at pre-issuance. Display and disposition bind to this value, not to
    #: the packet's current hash, which changes when the disposition is attached.
    issued_packet_sha256: str | None = None
    confirmed_pre_issuance_event_id: str | None = None
    confirmed_pre_issuance_at: datetime | None = None
    confirmed_closure_event_id: str | None = None
    confirmed_closure_at: datetime | None = None


def validate_packet_semantics(
    packet: DecisionReadinessPacket, context: SemanticContext
) -> tuple[str, ...]:
    """Return a tuple of failure codes. Empty means every semantic invariant holds."""
    failures: list[str] = []
    payload = packet.model_dump(mode="json")

    # 1. Consistent case, authorization, contract, environment, scope and data boundary.
    if packet.identity.case_id != context.case_id:
        failures.append("SEM-01_CASE_ID_MISMATCH")
    if packet.authorization_context.authorization_id != context.authorization.authorization_id:
        failures.append("SEM-01_AUTHORIZATION_MISMATCH")
    if (
        packet.authorization_context.use_case_contract_id
        != context.authorization.use_case_contract_id
    ):
        failures.append("SEM-01_USE_CASE_MISMATCH")
    for claim in packet.claim_ledger:
        if claim.case_id != context.case_id:
            failures.append("SEM-01_CLAIM_CASE_MISMATCH")
            break
    for result in packet.rule_results:
        if result.case_id != context.case_id:
            failures.append("SEM-01_RULE_CASE_MISMATCH")
            break

    # 2. Every material claim is SUPPORTED with exact evidence links, or the route stops.
    unsupported_material = [
        claim.claim_ref
        for claim in packet.claim_ledger
        if claim.materiality is Materiality.MATERIAL
        and (claim.support_state is not SupportState.SUPPORTED or not claim.evidence_links)
    ]
    if unsupported_material and packet.route is not Route.CANNOT_PROCEED:
        failures.append("SEM-02_MATERIAL_CLAIM_NOT_SUPPORTED")

    # 3. All cited excerpts reference manifest-listed active sources that passed checks.
    manifest_ids = {item.excerpt_id for item in packet.evidence_manifest}
    for item in packet.evidence_manifest:
        if f"{item.source_id}@{item.source_version}" not in context.eligible_source_keys:
            failures.append("SEM-03_CITED_SOURCE_NOT_ELIGIBLE")
            break
        if item.excerpt_id not in context.admitted_excerpt_ids:
            failures.append("SEM-03_EXCERPT_NOT_ADMITTED")
            break
    for claim in packet.claim_ledger:
        for link in claim.evidence_links:
            if link.excerpt_id not in manifest_ids:
                failures.append("SEM-03_CLAIM_CITES_UNLISTED_EXCERPT")
                break
            if not link.quote_verified:
                failures.append("SEM-03_QUOTE_NOT_VERIFIED")
                break

    # 4. Source and excerpt timestamps precede model, rule, packet and audit timestamps.
    packet_time = packet.identity.created_at
    latest_excerpt = max((item.retrieved_at for item in packet.evidence_manifest), default=None)
    if latest_excerpt and latest_excerpt > packet_time:
        failures.append("SEM-04_EXCERPT_AFTER_PACKET")
    latest_rule = max((result.evaluated_at for result in packet.rule_results), default=None)
    if latest_rule and latest_excerpt and latest_rule < latest_excerpt:
        failures.append("SEM-04_RULE_BEFORE_RETRIEVAL")
    if latest_rule and latest_rule > packet_time:
        failures.append("SEM-04_RULE_AFTER_PACKET")
    if packet.integrity.calculated_at < packet_time:
        failures.append("SEM-04_SEAL_BEFORE_PACKET")

    # 5. Versions match the authorization fixture's allowed set.
    allowed = context.authorization.allowed_component_versions
    lineage_checks = {
        "workflow": packet.version_lineage.workflow_version,
        "schema": packet.version_lineage.schema_version,
        "rule_catalog": packet.version_lineage.rule_catalog_version,
        "corpus": packet.version_lineage.corpus_version,
        "retrieval": packet.version_lineage.retrieval_version,
        "prompt_draft": packet.version_lineage.prompt_draft_version,
        "prompt_verify": packet.version_lineage.prompt_verify_version,
        "packet_schema": packet.version_lineage.packet_schema_version,
        "audit_chain": packet.version_lineage.audit_chain_version,
    }
    for key, value in lineage_checks.items():
        if allowed.get(key) != value:
            failures.append(f"SEM-05_VERSION_NOT_AUTHORIZED:{key}")
    for configuration_id in (
        packet.version_lineage.draft_model_configuration_id,
        packet.version_lineage.verifier_model_configuration_id,
    ):
        if configuration_id not in context.authorization.allowed_model_configuration_ids:
            failures.append("SEM-05_MODEL_CONFIG_NOT_AUTHORIZED")

    # 6. Only the two V1 routes exist.
    if packet.route not in {Route.HUMAN_REVIEW_REQUIRED, Route.CANNOT_PROCEED}:
        failures.append("SEM-06_ROUTE_NOT_PERMITTED")

    # 7. A HUMAN_REVIEW_REQUIRED packet has no unresolved material control failure.
    if packet.route is Route.HUMAN_REVIEW_REQUIRED:
        if any(result.is_mandatory_stop for result in packet.rule_results):
            failures.append("SEM-07_UNRESOLVED_MANDATORY_STOP")
        if packet.risk.inherent_risk is RiskLevel.CRITICAL:
            failures.append("SEM-07_CRITICAL_RISK_WITHOUT_STOP")

    # 8. Required fixed notices are present verbatim.
    present = {notice.notice_id for notice in packet.notices}
    if not REQUIRED_NOTICE_IDS.issubset(present):
        failures.append("SEM-08_MISSING_REQUIRED_NOTICE")
    for notice in packet.notices:
        expected = NOTICE_TEXT_BY_ID.get(notice.notice_id)
        if expected is not None and notice.text_en != expected:
            failures.append("SEM-08_NOTICE_TEXT_ALTERED")
            break

    # 9. Packet display requires a matching confirmed pre-issuance event.
    if packet.route is Route.HUMAN_REVIEW_REQUIRED:
        if not context.confirmed_pre_issuance_event_id:
            failures.append("SEM-09_NO_CONFIRMED_PRE_ISSUANCE")
        elif (
            packet.audit_binding.pre_issuance_event_id
            and packet.audit_binding.pre_issuance_event_id
            != context.confirmed_pre_issuance_event_id
        ):
            failures.append("SEM-09_PRE_ISSUANCE_BINDING_MISMATCH")

    # 10. A final disposition needs reverified authority, no self-review, a rationale, the
    #     exact packet version and hash, and a later closure event.
    disposition = packet.disposition
    if disposition is not None:
        if disposition.packet_id != packet.identity.packet_id:
            failures.append("SEM-10_DISPOSITION_PACKET_MISMATCH")
        if disposition.packet_version != packet.identity.packet_version:
            failures.append("SEM-10_DISPOSITION_VERSION_MISMATCH")
        expected_hash = context.issued_packet_sha256 or packet.integrity.packet_sha256
        if disposition.packet_sha256 != expected_hash:
            failures.append("SEM-10_DISPOSITION_HASH_MISMATCH")
        if disposition.reviewer_identity_id == packet.request_context.requester_identity_id:
            failures.append("SEM-10_SELF_REVIEW")
        if not disposition.human_rationale.strip():
            failures.append("SEM-10_MISSING_RATIONALE")
        if disposition.is_final:
            if not context.confirmed_closure_event_id:
                failures.append("SEM-10_NO_CONFIRMED_CLOSURE")
            elif context.confirmed_closure_event_id == context.confirmed_pre_issuance_event_id:
                failures.append("SEM-10_CLOSURE_NOT_DISTINCT")
            elif (
                context.confirmed_closure_at
                and context.confirmed_pre_issuance_at
                and context.confirmed_closure_at < context.confirmed_pre_issuance_at
            ):
                failures.append("SEM-10_CLOSURE_NOT_LATER")

    # 11. No action id, webhook, external target, record mutation or execution command.
    serialized = _flatten_strings(payload).casefold()
    for term in PROHIBITED_PACKET_TERMS:
        if term.casefold() in serialized:
            failures.append(f"SEM-11_PROHIBITED_TERM:{term}")

    # The seal must verify against its own preimage.
    if not verify_packet_hash(payload):
        failures.append("SEM-12_SEAL_DOES_NOT_VERIFY")

    return tuple(dict.fromkeys(failures))


def _flatten_strings(value: Any) -> str:
    """Concatenate every string in a nested structure, for the prohibited-term scan.

    Notice text is excluded: the fixed notices legitimately contain words such as
    "executed" and "transmitted" while stating that no such thing happened.
    """
    parts: list[str] = []

    def walk(node: Any, key: str | None = None) -> None:
        if key == "notices":
            return
        if isinstance(node, str):
            parts.append(node)
        elif isinstance(node, dict):
            for child_key, child in node.items():
                walk(child, child_key)
        elif isinstance(node, list | tuple):
            for child in node:
                walk(child, key)

    walk(value)
    return " ".join(parts)


def build_risk_profile(
    *,
    material_claim_count: int,
    uncertainty: tuple[UncertaintyRecord, ...],
    conflicts: tuple[str, ...],
    quarantined_sources: tuple[str, ...],
) -> RiskProfile:
    """Dominant-factor risk. A CRITICAL or UNKNOWN factor can never be averaged down."""
    from app.domain.enums import RISK_ORDER
    from app.schemas.reasoning import RiskFactor

    factors = [
        RiskFactor(
            factor_id="RF-EVIDENCE",
            label_en="Evidence sufficiency",
            label_ar="كفاية الأدلة",
            level=RiskLevel.LOW if material_claim_count else RiskLevel.UNKNOWN,
            rationale=(
                f"{material_claim_count} material claim(s) carry exact citations."
                if material_claim_count
                else "No material claim carries a citation."
            ),
        ),
        RiskFactor(
            factor_id="RF-CONFLICT",
            label_en="Source conflict",
            label_ar="تعارض المصادر",
            level=RiskLevel.CRITICAL if conflicts else RiskLevel.LOW,
            rationale=(
                "A declared material conflict between active sources applies."
                if conflicts
                else "No declared material conflict applies to this request."
            ),
        ),
        RiskFactor(
            factor_id="RF-UNCERTAINTY",
            label_en="Residual uncertainty",
            label_ar="عدم اليقين المتبقي",
            level=RiskLevel.MODERATE if uncertainty else RiskLevel.LOW,
            rationale=f"{len(uncertainty)} uncertainty record(s) are attached to this packet.",
        ),
        RiskFactor(
            factor_id="RF-ISOLATION",
            label_en="Content isolation",
            label_ar="عزل المحتوى",
            level=RiskLevel.MODERATE if quarantined_sources else RiskLevel.LOW,
            rationale=(
                f"{len(quarantined_sources)} quarantined source(s) were excluded before retrieval."
                if quarantined_sources
                else "No quarantined source was relevant to this request."
            ),
        ),
    ]
    dominant = max(factors, key=lambda factor: RISK_ORDER[factor.level])
    seniority = (
        "Manager grade or above with restricted records authorisation"
        if dominant.level in {RiskLevel.CRITICAL, RiskLevel.HIGH}
        else "Manager grade or above"
    )
    depth = (
        "Full evidence re-read with written escalation"
        if dominant.level in {RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.UNKNOWN}
        else "Standard citation and rule-result review"
    )
    return RiskProfile(
        factors=tuple(factors),
        dominant_factor_id=dominant.factor_id,
        inherent_risk=dominant.level,
        reviewer_seniority_required=seniority,
        review_depth_required=depth,
    )


def packet_created_at() -> datetime:
    return utc_now()
