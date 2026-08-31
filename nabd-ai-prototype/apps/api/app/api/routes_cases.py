"""Case intake, processing, packet, evidence, audit and lineage routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentIdentity, DbSession, RequesterIdentity, load_visible_case
from app.domain.canonical import verify_packet_hash
from app.domain.enums import (
    CASE_STATE_STAGE,
    AuditEventType,
    AuditOutcome,
    CaseState,
    DemoRole,
    Route,
)
from app.domain.errors import (
    AccessDeniedError,
    IllegalTransitionError,
    NotFoundError,
    StopError,
)
from app.domain.ids import new_case_id
from app.domain.limits import limit_register_payload
from app.domain.reason_codes import REASON_MESSAGES, ReasonCode
from app.repositories.tables import (
    CaseRow,
    CaseStateTransitionRow,
    ClaimEvidenceLinkRow,
    DecisionPacketRow,
    DeterministicResultRow,
    EvidenceExcerptRow,
    GeneratedClaimRow,
    SourcePageRow,
    SourceVersionRow,
)
from app.schemas.api import (
    AuditEventView,
    AuditResponse,
    CaseListResponse,
    CaseProgressResponse,
    CaseSummary,
    CreateCaseRequest,
    ExcerptResponse,
    LineageEdge,
    LineageNode,
    LineageResponse,
    PacketResponse,
    RuleResultView,
    SourcePageResponse,
    StateTransitionView,
)
from app.services import audit
from app.services.fixtures import (
    load_corpus_fixtures,
    load_use_case_contract,
    primary_authorization,
)
from app.services.orchestrator import build_case_row, process_case
from app.services.review import displayable_packet

router = APIRouter(prefix="/api/v1", tags=["cases"])


def _reason_message(code: str | None) -> str | None:
    if not code:
        return None
    try:
        return REASON_MESSAGES[ReasonCode(code)]
    except (KeyError, ValueError):
        return None


def _packet_row(db: DbSession, case_id: str) -> DecisionPacketRow | None:
    return (
        db.execute(
            select(DecisionPacketRow)
            .where(DecisionPacketRow.case_id == case_id)
            .order_by(DecisionPacketRow.packet_version.desc())
        )
        .scalars()
        .first()
    )


def _summary(db: DbSession, case: CaseRow, identity_role: DemoRole) -> CaseSummary:
    state = CaseState(case.current_state)
    packet = _packet_row(db, case.case_id)
    actions: list[str] = []
    if state is CaseState.AUTHORIZATION_PREFLIGHT and identity_role is DemoRole.REQUESTER:
        actions.append("PROCESS_CASE")
    if state is CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW:
        actions.append("VIEW_PACKET")
        if identity_role is DemoRole.REVIEWER:
            actions.append("SUBMIT_TEST_DISPOSITION")
    if state is CaseState.CLOSED_DECISION_SUPPORT_RECORD:
        actions.append("VIEW_PACKET")
    return CaseSummary(
        case_id=case.case_id,
        requester_identity_id=case.requester_identity_id,
        normalised_question=case.normalised_question,
        current_state=case.current_state,
        stage=CASE_STATE_STAGE.get(state),
        route=case.route,
        reason_code=case.reason_code,
        reason_message=_reason_message(case.reason_code),
        submitted_at=case.submitted_at,
        updated_at=case.updated_at,
        packet_available=bool(packet and packet.displayable),
        permissible_next_actions=tuple(actions),
    )


@router.post("/cases", response_model=CaseSummary, status_code=201)
def create_case(
    payload: CreateCaseRequest, identity: RequesterIdentity, db: DbSession
) -> CaseSummary:
    from app.services.kill_switch import kill_switch_active

    if kill_switch_active(db):
        raise StopError(ReasonCode.EMERGENCY_STOP_ACTIVE)

    case = build_case_row(
        case_id=new_case_id(),
        identity=identity,
        raw_question=payload.question,
        authorization_id=primary_authorization().authorization_id,
        use_case_contract_id=load_use_case_contract().use_case_contract_id,
    )
    db.add(case)
    db.flush()
    audit.record(
        db,
        event_type=AuditEventType.CASE_CREATED,
        actor_id=identity.identity_id,
        actor_kind="HUMAN_DEMO_IDENTITY",
        outcome=AuditOutcome.RECORDED,
        case_id=case.case_id,
        payload_reference=f"question_sha256={case.question_sha256}",
    )
    return _summary(db, case, identity.role)


@router.post("/cases/{case_id}/process", response_model=CaseSummary)
def process(case_id: str, identity: RequesterIdentity, db: DbSession) -> CaseSummary:
    case = load_visible_case(db, case_id, identity)
    current = CaseState(case.current_state)
    if current is not CaseState.AUTHORIZATION_PREFLIGHT:
        # Replaying processing on a case that has already advanced is an illegal edge.
        raise IllegalTransitionError(
            case_id=case_id,
            from_state=current,
            to_state=CaseState.ACTOR_AND_SESSION_VERIFICATION,
        )
    process_case(db, case, identity)
    return _summary(db, case, identity.role)


@router.get("/cases", response_model=CaseListResponse)
def list_cases(identity: CurrentIdentity, db: DbSession) -> CaseListResponse:
    if identity.role is DemoRole.ADMINISTRATOR:
        raise AccessDeniedError(ReasonCode.ACCESS_DENIED)
    query = select(CaseRow).where(CaseRow.business_scope_id == identity.business_scope_id)
    if identity.role is DemoRole.REQUESTER:
        query = query.where(CaseRow.requester_identity_id == identity.identity_id)
    rows = db.execute(query.order_by(CaseRow.submitted_at.desc())).scalars().all()
    if identity.role is DemoRole.REVIEWER:
        rows = [row for row in rows if row.requester_identity_id != identity.identity_id]
    return CaseListResponse(cases=tuple(_summary(db, row, identity.role) for row in rows))


@router.get("/cases/{case_id}", response_model=CaseSummary)
def read_case(case_id: str, identity: CurrentIdentity, db: DbSession) -> CaseSummary:
    case = load_visible_case(db, case_id, identity)
    return _summary(db, case, identity.role)


@router.get("/cases/{case_id}/progress", response_model=CaseProgressResponse)
def read_progress(case_id: str, identity: CurrentIdentity, db: DbSession) -> CaseProgressResponse:
    case = load_visible_case(db, case_id, identity)
    transitions = (
        db.execute(
            select(CaseStateTransitionRow)
            .where(CaseStateTransitionRow.case_id == case_id)
            .order_by(CaseStateTransitionRow.sequence.asc())
        )
        .scalars()
        .all()
    )
    results = (
        db.execute(
            select(DeterministicResultRow)
            .where(DeterministicResultRow.case_id == case_id)
            .order_by(
                DeterministicResultRow.evaluated_at.asc(),
                DeterministicResultRow.precedence_rank.asc(),
            )
        )
        .scalars()
        .all()
    )
    return CaseProgressResponse(
        case=_summary(db, case, identity.role),
        transitions=tuple(
            StateTransitionView(
                sequence=row.sequence,
                from_state=row.from_state,
                to_state=row.to_state,
                reason_code=row.reason_code,
                reason_message=_reason_message(row.reason_code),
                actor_id=row.actor_id,
                occurred_at=row.occurred_at,
            )
            for row in transitions
        ),
        rule_results=tuple(
            RuleResultView(
                rule_id=row.rule_id,
                rule_version=row.rule_version,
                outcome=row.outcome,
                reason_code=row.reason_code,
                effect=row.effect,
                precedence_rank=row.precedence_rank,
                detail=str((row.payload or {}).get("detail", "")),
                evaluated_at=row.evaluated_at,
            )
            for row in results
        ),
        limits=tuple(limit_register_payload()),
        stop_record=case.stop_record,
    )


@router.get("/cases/{case_id}/packet", response_model=PacketResponse)
def read_packet(case_id: str, identity: CurrentIdentity, db: DbSession) -> PacketResponse:
    case = load_visible_case(db, case_id, identity)
    if case.route == Route.CANNOT_PROCEED.value:
        raise NotFoundError(ReasonCode.PACKET_NOT_AVAILABLE, case_id=case_id)
    row = displayable_packet(db, case_id)
    audit.record(
        db,
        event_type=AuditEventType.PACKET_VIEWED,
        actor_id=identity.identity_id,
        actor_kind="HUMAN_DEMO_IDENTITY",
        outcome=AuditOutcome.RECORDED,
        case_id=case_id,
        payload_reference=f"packet_sha256={row.packet_sha256}",
    )
    return PacketResponse(
        packet=row.payload,
        canonical_sha256=row.packet_sha256,
        seal_verified=verify_packet_hash(row.payload),
    )


@router.get("/evidence/{excerpt_id}", response_model=ExcerptResponse)
def read_excerpt(excerpt_id: str, identity: CurrentIdentity, db: DbSession) -> ExcerptResponse:
    row = db.get(EvidenceExcerptRow, excerpt_id)
    if row is None:
        raise NotFoundError(ReasonCode.NOT_FOUND)
    # Scope the excerpt through its case, so evidence inherits case visibility exactly.
    case = load_visible_case(db, row.case_id, identity)
    corpus = load_corpus_fixtures()
    item = corpus.by_key(row.source_version_key)
    revocation = corpus.revocation_for(row.source_version_key)
    return ExcerptResponse(
        excerpt_id=row.excerpt_id,
        case_id=case.case_id,
        source_id=row.source_id,
        source_version=row.source_version,
        source_title=item.title if item else "",
        authority_class=item.authority_class.value if item else "",
        lifecycle=item.lifecycle.value if item else "",
        page_number=row.page_number,
        section_heading=row.section_heading,
        char_start=row.char_start,
        char_end=row.char_end,
        text=row.text,
        text_sha256=row.text_sha256,
        source_sha256=row.source_sha256,
        trust_label="UNTRUSTED_CONTENT",
        citation_label=(
            f"{row.source_id}@{row.source_version} p.{row.page_number} "
            f"[{row.char_start}-{row.char_end}]"
        ),
        revocation_warning=revocation.reason_en if revocation else None,
    )


@router.get("/sources/{source_id}/pages/{page}", response_model=SourcePageResponse)
def read_source_page(
    source_id: str, page: int, identity: CurrentIdentity, db: DbSession
) -> SourcePageResponse:
    if identity.role is DemoRole.ADMINISTRATOR:
        raise AccessDeniedError(ReasonCode.ACCESS_DENIED)
    corpus = load_corpus_fixtures()
    versions = [
        item
        for item in corpus.by_source_id(source_id)
        if item.business_scope_id == identity.business_scope_id
    ]
    if not versions:
        raise NotFoundError(ReasonCode.NOT_FOUND)
    # Quarantined sources are never rendered: their body is instruction-like content.
    readable = [item for item in versions if not item.is_quarantined]
    if not readable:
        raise NotFoundError(ReasonCode.SOURCE_QUARANTINED)
    item = sorted(readable, key=lambda entry: entry.source_version, reverse=True)[0]

    page_row = db.get(SourcePageRow, f"{item.source_key}#p{page}")
    if page_row is None:
        raise NotFoundError(ReasonCode.NOT_FOUND)
    version_row = db.get(SourceVersionRow, item.source_key)
    revocation = corpus.revocation_for(item.source_key)
    return SourcePageResponse(
        source_id=item.source_id,
        source_version=item.source_version,
        title=item.title,
        lifecycle=version_row.lifecycle if version_row else item.lifecycle.value,
        page_number=page_row.page_number,
        page_count=item.page_count,
        section_headings=tuple(page_row.section_headings or ()),
        char_start=page_row.char_start,
        char_end=page_row.char_end,
        text=page_row.page_text,
        trust_label="UNTRUSTED_CONTENT",
        revocation_warning=revocation.reason_en if revocation else None,
    )


@router.get("/cases/{case_id}/audit", response_model=AuditResponse)
def read_audit(case_id: str, identity: CurrentIdentity, db: DbSession) -> AuditResponse:
    case = load_visible_case(db, case_id, identity)
    rows = audit.load_chain(db, case.case_id)
    verification = audit.verify_chain(db, case.case_id)
    events = tuple(
        AuditEventView(
            event_id=row.event_id,
            sequence=row.sequence,
            event_type=row.event_type,
            application_time=row.application_time,
            actor_id=row.actor_id,
            actor_kind=row.actor_kind,
            outcome=row.outcome,
            reason_code=row.reason_code,
            severity=row.severity,
            from_state=row.from_state,
            to_state=row.to_state,
            object_kind=((row.payload or {}).get("binding") or {}).get("object_kind"),
            object_id=((row.payload or {}).get("binding") or {}).get("object_id"),
            previous_event_hash=row.previous_event_hash,
            event_hash=row.event_hash,
            confirmed=row.confirmed,
        )
        for row in rows
    )
    return AuditResponse(
        case_id=case.case_id,
        events=events,
        verification=verification.model_dump(mode="json"),
    )


@router.get("/cases/{case_id}/lineage", response_model=LineageResponse)
def read_lineage(case_id: str, identity: CurrentIdentity, db: DbSession) -> LineageResponse:
    case = load_visible_case(db, case_id, identity)
    nodes: list[LineageNode] = []
    edges: list[LineageEdge] = []

    excerpts = (
        db.execute(
            select(EvidenceExcerptRow)
            .where(EvidenceExcerptRow.case_id == case_id)
            .order_by(EvidenceExcerptRow.rank.asc())
        )
        .scalars()
        .all()
    )
    claims = (
        db.execute(
            select(GeneratedClaimRow)
            .where(GeneratedClaimRow.case_id == case_id)
            .order_by(GeneratedClaimRow.claim_ref.asc())
        )
        .scalars()
        .all()
    )
    links = (
        db.execute(select(ClaimEvidenceLinkRow).where(ClaimEvidenceLinkRow.case_id == case_id))
        .scalars()
        .all()
    )
    results = (
        db.execute(
            select(DeterministicResultRow)
            .where(DeterministicResultRow.case_id == case_id)
            .order_by(DeterministicResultRow.precedence_rank.asc())
        )
        .scalars()
        .all()
    )
    packet = _packet_row(db, case_id)

    seen_sources: set[str] = set()
    for excerpt in excerpts:
        if excerpt.source_version_key not in seen_sources:
            seen_sources.add(excerpt.source_version_key)
            nodes.append(
                LineageNode(
                    node_id=f"source:{excerpt.source_version_key}",
                    kind="SOURCE",
                    label=excerpt.source_version_key,
                    detail="Frozen synthetic source version",
                )
            )
        nodes.append(
            LineageNode(
                node_id=f"excerpt:{excerpt.excerpt_id}",
                kind="EXCERPT",
                label=f"p.{excerpt.page_number} [{excerpt.char_start}-{excerpt.char_end}]",
                detail=excerpt.section_heading,
            )
        )
        edges.append(
            LineageEdge(
                source=f"source:{excerpt.source_version_key}",
                target=f"excerpt:{excerpt.excerpt_id}",
                relation="RETRIEVED_AS",
            )
        )

    for claim in claims:
        nodes.append(
            LineageNode(
                node_id=f"claim:{claim.claim_id}",
                kind="CLAIM",
                label=f"{claim.claim_ref} ({claim.materiality})",
                detail=claim.support_state,
            )
        )
    for link in links:
        edges.append(
            LineageEdge(
                source=f"excerpt:{link.excerpt_id}",
                target=f"claim:{link.claim_id}",
                relation="SUPPORTS" if link.quote_verified else "CITED_UNVERIFIED",
            )
        )

    seen_rules: set[str] = set()
    for result in results:
        node_id = f"rule:{result.rule_id}"
        if node_id in seen_rules:
            continue
        seen_rules.add(node_id)
        nodes.append(
            LineageNode(
                node_id=node_id,
                kind="RULE",
                label=f"{result.rule_id} ({result.outcome})",
                detail=result.reason_code,
            )
        )
        for claim in claims:
            edges.append(
                LineageEdge(
                    source=f"claim:{claim.claim_id}", target=node_id, relation="EVALUATED_BY"
                )
            )
            break

    route_id = f"route:{case.route or 'PENDING'}"
    nodes.append(
        LineageNode(node_id=route_id, kind="ROUTE", label=case.route or "PENDING", detail="")
    )
    for node_id in sorted(seen_rules):
        edges.append(LineageEdge(source=node_id, target=route_id, relation="DETERMINES"))

    if packet is not None:
        packet_node = f"packet:{packet.packet_id}"
        nodes.append(
            LineageNode(
                node_id=packet_node,
                kind="PACKET",
                label=f"v{packet.packet_version}",
                detail=packet.packet_sha256[:16],
            )
        )
        edges.append(LineageEdge(source=route_id, target=packet_node, relation="SEALED_INTO"))

    return LineageResponse(case_id=case_id, nodes=tuple(nodes), edges=tuple(edges))


def lineage_payload(_: Any) -> None:  # pragma: no cover - placeholder for typing symmetry
    return None
