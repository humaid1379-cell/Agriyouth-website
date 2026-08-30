"""Demo session, identity and use-case contract routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentIdentity, DbSession
from app.domain.notices import notices_payload
from app.domain.versions import (
    BRAND_STATEMENT_AR,
    BRAND_STATEMENT_EN,
    DATA_BOUNDARY_ID,
    ENVIRONMENT_ID,
)
from app.schemas.api import (
    DemoIdentityOption,
    DemoSessionRequest,
    DemoSessionResponse,
    MeResponse,
    NoticePayload,
    UseCaseResponse,
)
from app.services.fixtures import contract_extras, load_identities, load_use_case_contract
from app.services.identity import create_session, selectable_identities

router = APIRouter(prefix="/api/v1", tags=["session"])


def _notices() -> tuple[NoticePayload, ...]:
    return tuple(
        NoticePayload(
            notice_id=notice["notice_id"],
            heading_en=notice["heading_en"],
            text_en=notice["text_en"],
            heading_ar=notice["heading_ar"],
            text_ar=notice["text_ar"],
        )
        for notice in notices_payload()
    )


@router.get("/demo/identities", response_model=list[DemoIdentityOption])
def list_demo_identities() -> list[DemoIdentityOption]:
    """Selectable synthetic profiles.

    Denial fixtures (expired, revoked, unknown, cross-scope) are deliberately absent: they
    exist for tests, not for the browser.
    """
    return [
        DemoIdentityOption(
            identity_id=identity.identity_id,
            display_name_en=identity.display_name_en,
            display_name_ar=identity.display_name_ar,
            role=identity.role,
            capabilities=identity.capabilities,
            prohibitions=identity.prohibitions,
        )
        for identity in selectable_identities()
    ]


@router.post("/demo/session", response_model=DemoSessionResponse)
def create_demo_session(payload: DemoSessionRequest, db: DbSession) -> DemoSessionResponse:
    token, assertion = create_session(db, payload.identity_id)
    return DemoSessionResponse(
        token=token,
        identity_id=assertion.identity_id,
        role=assertion.role,
        expires_at=assertion.expires_at,
        notices=_notices(),
    )


@router.get("/me", response_model=MeResponse)
def read_me(identity: CurrentIdentity) -> MeResponse:
    fixture = load_identities()[identity.identity_id]
    return MeResponse(
        identity_id=identity.identity_id,
        display_name_en=fixture.display_name_en,
        display_name_ar=fixture.display_name_ar,
        role=identity.role,
        role_id=identity.role_id,
        business_scope_id=identity.business_scope_id,
        environment_id=ENVIRONMENT_ID,
        data_boundary_id=DATA_BOUNDARY_ID,
        session_expires_at=identity.expires_at,
        capabilities=fixture.capabilities,
        prohibitions=fixture.prohibitions,
        notices=_notices(),
        brand_statement_en=BRAND_STATEMENT_EN,
        brand_statement_ar=BRAND_STATEMENT_AR,
    )


@router.get("/use-case", response_model=UseCaseResponse)
def read_use_case() -> UseCaseResponse:
    contract = load_use_case_contract()
    extras = contract_extras()
    return UseCaseResponse(
        use_case_contract_id=contract.use_case_contract_id,
        title_en=contract.title_en,
        title_ar=contract.title_ar,
        description_en=contract.description_en,
        description_ar=contract.description_ar,
        permitted_purpose=contract.permitted_purpose,
        permitted_question_kinds=contract.permitted_question_kinds,
        excluded_scope_terms=contract.excluded_scope_terms,
        excluded_outcomes=contract.excluded_outcomes,
        max_question_chars=contract.max_question_chars,
        min_question_chars=int(extras.get("min_question_chars", 20)),
        business_scope_id=contract.business_scope_id,
        data_boundary_id=contract.data_boundary_id,
    )
