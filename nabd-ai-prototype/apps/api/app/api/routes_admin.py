"""Administrator routes: configuration inspection, kill switch, audit verification, TEVV.

The administrator operates controls. It cannot grant authorization, submit or review a
case, modify source content, or read case content.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import AdminIdentity, DbSession
from app.config import get_settings
from app.domain.enums import (
    AuthorizationStatus,
    OperationalStatus,
    StatusEvidence,
)
from app.domain.errors import AccessDeniedError, NotFoundError
from app.domain.fsm import transition_table
from app.domain.limits import limit_register_payload
from app.domain.prohibited import inventory_payload
from app.domain.reason_codes import ReasonCode
from app.domain.versions import COMPONENT_VERSIONS, ENVIRONMENT_ID
from app.repositories.tables import TevvResultRow, TevvRunRow
from app.rules.catalog import catalog_payload
from app.schemas.api import (
    AuditVerifyRequest,
    ConfigurationResponse,
    KillSwitchRequest,
    KillSwitchResponse,
    TevvResultView,
    TevvRunRequest,
    TevvRunResponse,
)
from app.services import audit
from app.services.fixtures import load_corpus_fixtures, load_model_configurations
from app.services.kill_switch import current_state, set_kill_switch

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _kill_switch_response(db: DbSession) -> KillSwitchResponse:
    state = current_state(db)
    return KillSwitchResponse(
        active=state.active,
        changed_at=state.changed_at,
        changed_by=state.changed_by,
        reason=state.reason,
    )


@router.get("/configuration", response_model=ConfigurationResponse)
def read_configuration(identity: AdminIdentity, db: DbSession) -> ConfigurationResponse:
    settings = get_settings()
    corpus = load_corpus_fixtures()
    configurations = load_model_configurations()
    return ConfigurationResponse(
        environment_id=ENVIRONMENT_ID,
        component_versions=dict(COMPONENT_VERSIONS),
        corpus_manifest_sha256=corpus.manifest_sha256,
        rule_catalog=tuple(catalog_payload()),
        limits=tuple(limit_register_payload()),
        state_machine=tuple(transition_table()),
        model_configurations=tuple(
            {
                "model_configuration_id": configuration.model_configuration_id,
                "task_role": configuration.task_role.value,
                "model_revision": configuration.model_revision,
                "prompt_version": configuration.prompt_version,
                "output_schema_id": configuration.output_schema_id,
                "mode": configuration.mode.value,
                "tool_calling_enabled": configuration.tool_calling_enabled,
                "fallback_enabled": configuration.fallback_enabled,
                "timeout_seconds": configuration.timeout_seconds,
                "max_same_endpoint_retries": configuration.max_same_endpoint_retries,
                "built": configuration.built.value,
                "integration": configuration.integration.value,
                "operational": configuration.operational.value,
                "authorization": configuration.authorization.value,
            }
            for configuration in sorted(
                configurations.values(), key=lambda c: c.model_configuration_id
            )
        ),
        settings=settings.redacted(),
        prohibited_integrations=tuple(inventory_payload()),
        kill_switch=_kill_switch_response(db),
        status={
            "built": StatusEvidence.NOT_EVIDENCED.value,
            "integration": StatusEvidence.NOT_EVIDENCED.value,
            "operational": OperationalStatus.NOT_EVIDENCED.value,
            "authorization": AuthorizationStatus.NOT_GRANTED.value,
        },
    )


@router.post("/kill-switch", response_model=KillSwitchResponse)
def toggle_kill_switch(
    payload: KillSwitchRequest, identity: AdminIdentity, db: DbSession
) -> KillSwitchResponse:
    set_kill_switch(db, active=payload.active, actor_id=identity.identity_id, reason=payload.reason)
    return _kill_switch_response(db)


@router.post("/audit/verify")
def verify_audit(
    payload: AuditVerifyRequest, identity: AdminIdentity, db: DbSession
) -> dict[str, object]:
    verification = audit.verify_chain(db, payload.case_id)
    return verification.model_dump(mode="json")


@router.post("/tevv/run", response_model=TevvRunResponse)
def run_tevv(payload: TevvRunRequest, identity: AdminIdentity, db: DbSession) -> TevvRunResponse:
    settings = get_settings()
    if settings.app_env not in {"local", "demo", "test"}:
        raise AccessDeniedError(ReasonCode.ACCESS_DENIED)

    from app.services.tevv import execute_tevv_run

    run = execute_tevv_run(
        db, executor=identity.identity_id, scenario_ids=payload.scenario_ids or None
    )
    return _tevv_response(db, run.tevv_run_id)


@router.get("/tevv/runs/{tevv_run_id}", response_model=TevvRunResponse)
def read_tevv_run(tevv_run_id: str, identity: AdminIdentity, db: DbSession) -> TevvRunResponse:
    return _tevv_response(db, tevv_run_id)


def _tevv_response(db: DbSession, tevv_run_id: str) -> TevvRunResponse:
    from app.services.tevv import scenario_index

    run = db.get(TevvRunRow, tevv_run_id)
    if run is None:
        raise NotFoundError(ReasonCode.NOT_FOUND)
    rows = (
        db.execute(
            select(TevvResultRow)
            .where(TevvResultRow.tevv_run_id == tevv_run_id)
            .order_by(TevvResultRow.scenario_id.asc(), TevvResultRow.repetition.asc())
        )
        .scalars()
        .all()
    )
    catalog = scenario_index()
    return TevvRunResponse(
        tevv_run_id=run.tevv_run_id,
        plan_version=run.plan_version,
        executor=run.executor,
        started_at=run.started_at,
        completed_at=run.completed_at,
        component_versions=run.component_versions,
        summary=run.summary,
        results=tuple(
            TevvResultView(
                scenario_id=row.scenario_id,
                title=catalog.get(row.scenario_id, {}).get("title", ""),
                category=catalog.get(row.scenario_id, {}).get("category", ""),
                repetition=row.repetition,
                status=row.status,
                expected=row.expected,
                actual=row.actual,
                case_id=row.case_id,
                trace_id=row.trace_id,
                defect_ids=tuple(row.defect_ids or ()),
                executed_at=row.executed_at,
            )
            for row in rows
        ),
    )
