"""Reviewer queue and test-only disposition routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession, ReviewerIdentity, load_visible_case
from app.api.routes_cases import _summary
from app.schemas.api import CaseListResponse, DispositionRequest, DispositionResponse
from app.services.review import review_queue, submit_disposition

router = APIRouter(prefix="/api/v1", tags=["review"])


@router.get("/review/queue", response_model=CaseListResponse)
def read_review_queue(identity: ReviewerIdentity, db: DbSession) -> CaseListResponse:
    rows = review_queue(db, identity)
    return CaseListResponse(cases=tuple(_summary(db, row, identity.role) for row in rows))


@router.post("/cases/{case_id}/dispositions", response_model=DispositionResponse, status_code=201)
def create_disposition(
    case_id: str, payload: DispositionRequest, identity: ReviewerIdentity, db: DbSession
) -> DispositionResponse:
    case = load_visible_case(db, case_id, identity)
    outcome = submit_disposition(
        db,
        case=case,
        identity=identity,
        disposition_value=payload.disposition_value,
        rationale=payload.human_rationale,
        expected_packet_sha256=payload.packet_sha256,
    )
    return DispositionResponse(
        case_id=outcome.case_id,
        disposition_id=outcome.disposition.disposition_id,
        disposition_value=outcome.disposition.disposition_value,
        is_final=outcome.is_final,
        terminal_state=outcome.terminal_state.value,
        closure_event_id=outcome.closure_event_id,
        packet_sha256=outcome.packet.integrity.packet_sha256,
        non_execution_notice=outcome.disposition.non_execution_notice,
    )
