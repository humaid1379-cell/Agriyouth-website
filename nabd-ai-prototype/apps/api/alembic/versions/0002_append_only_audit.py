"""Append-only audit enforcement and least-privilege grants.

Two independent controls protect confirmed audit events:

1. A ``BEFORE UPDATE OR DELETE`` trigger that raises an exception.
2. Table grants that give the application role ``INSERT`` and ``SELECT`` only.

Either alone would be bypassable by a mistake in the other. Both are asserted by the
audit mutation-denial tests.

Revision ID: 0002_append_only_audit
Revises: 0001_initial_schema
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_append_only_audit"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "nabd_app"

READ_WRITE_TABLES = (
    "cases",
    "case_state_transitions",
    "demo_sessions",
    "evidence_excerpts",
    "model_runs",
    "generated_claims",
    "claim_evidence_links",
    "deterministic_results",
    "uncertainty_records",
    "decision_packets",
    "human_dispositions",
    "kill_switch_events",
    "tevv_runs",
    "tevv_results",
    "defects",
    "evidence_records",
    "status_records",
)

READ_ONLY_TABLES = (
    "demo_identities",
    "authorization_decisions",
    "use_case_contracts",
    "source_records",
    "source_versions",
    "source_pages",
    "source_blocks",
)

TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION nabd_reject_audit_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION
    'audit_events is append-only: % on event_id % is rejected', TG_OP, OLD.event_id
    USING ERRCODE = '42501';
END;
$$ LANGUAGE plpgsql;
"""


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        # SQLite unit-test databases enforce append-only in the repository layer only.
        return

    op.execute(TRIGGER_FUNCTION)
    op.execute(
        """
        CREATE TRIGGER trg_audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION nabd_reject_audit_mutation();
        """
    )

    bind = op.get_bind()
    role_exists = bind.exec_driver_sql(
        f"SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}'"
    ).scalar()
    if not role_exists:
        return

    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    for table in READ_WRITE_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE {table} TO {APP_ROLE}")
    for table in READ_ONLY_TABLES:
        op.execute(f"GRANT SELECT ON TABLE {table} TO {APP_ROLE}")
    # The application may append and read audit events. It may never rewrite history.
    op.execute(f"GRANT SELECT, INSERT ON TABLE audit_events TO {APP_ROLE}")
    op.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON TABLE audit_events FROM {APP_ROLE}")
    # No source content mutation from the runtime role, under any code path.
    for table in READ_ONLY_TABLES:
        op.execute(f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE {table} FROM {APP_ROLE}")
    op.execute(f"GRANT SELECT ON TABLE alembic_version TO {APP_ROLE}")


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_append_only ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS nabd_reject_audit_mutation()")
