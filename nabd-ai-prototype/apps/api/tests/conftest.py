"""Test harness.

Integration tests run against a real PostgreSQL database so that the append-only trigger,
the least-privilege grants and the lexical retrieval index are exercised rather than
assumed. Tests marked ``unit`` may use SQLite, which is the only place the specification
permits it.

Critical audit events commit inside the service layer by design, so isolation is by
truncation between tests rather than by an outer transaction that could never roll them
back.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[3]

# The operational scripts are the supported entry points for seeding, schema export and
# evidence generation, so the tests exercise those exact modules rather than a parallel
# test-only implementation.
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
DEFAULT_TEST_DSN = (
    "postgresql+psycopg://nabd_owner:nabd_owner_demo@127.0.0.1:5432/nabd_prototype_test"
)

#: Tables truncated between tests. Corpus and fixture tables are seeded once and reused.
TRANSACTIONAL_TABLES = (
    "claim_evidence_links",
    "generated_claims",
    "deterministic_results",
    "uncertainty_records",
    "human_dispositions",
    "decision_packets",
    "evidence_excerpts",
    "model_runs",
    "case_state_transitions",
    "tevv_results",
    "tevv_runs",
    "audit_events",
    "kill_switch_events",
    "demo_sessions",
    "cases",
    "defects",
    "evidence_records",
    "status_records",
)


def pytest_configure(config: pytest.Config) -> None:
    """Bind the suite to a test database, overriding any ambient ``DATABASE_URL``.

    The suite truncates tables between tests, so inheriting a developer's ``DATABASE_URL``
    would let a test run destroy a working database. ``TEST_DATABASE_URL`` is the only way
    to redirect it, and the target name must still identify itself as a test database.
    """
    os.environ["APP_ENV"] = "test"
    os.environ["MODEL_MODE"] = "mock"
    dsn = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DSN)
    database_name = dsn.rsplit("/", 1)[-1].split("?")[0]
    if "test" not in database_name:
        raise pytest.UsageError(
            f"refusing to run destructive tests against database {database_name!r}; "
            "TEST_DATABASE_URL must name a test database"
        )
    os.environ["DATABASE_URL"] = dsn


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    from alembic import command
    from alembic.config import Config

    from app.repositories.database import build_engine, reset_engine

    dsn = os.environ["DATABASE_URL"]
    built = build_engine(dsn)
    reset_engine(built)

    alembic_config = Config(str(REPO_ROOT / "apps" / "api" / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(REPO_ROOT / "apps" / "api" / "alembic"))
    alembic_config.set_main_option("sqlalchemy.url", dsn)
    command.upgrade(alembic_config, "head")

    yield built
    built.dispose()


@pytest.fixture(scope="session")
def seeded(engine: Engine) -> Engine:
    """Seed the frozen corpus and control-plane fixtures once for the whole session."""
    from seed_synthetic_corpus import seed

    seed(reset=True, render_pdf=False)
    return engine


@pytest.fixture()
def db(seeded: Engine) -> Generator[Session, None, None]:
    from app.repositories.database import get_session_factory

    with seeded.begin() as connection:
        connection.execute(
            text(f"TRUNCATE {', '.join(TRANSACTIONAL_TABLES)} RESTART IDENTITY CASCADE")
        )

    session = get_session_factory()()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def client(db: Session):  # type: ignore[no-untyped-def]
    """FastAPI test client bound to the same database as ``db``."""
    from fastapi.testclient import TestClient

    from app.main import create_app

    return TestClient(create_app())


@pytest.fixture()
def requester_identity():  # type: ignore[no-untyped-def]
    from app.services.identity import assertion_for_fixture

    return assertion_for_fixture("requester.analyst@demo.nabd.local")


@pytest.fixture()
def reviewer_identity():  # type: ignore[no-untyped-def]
    from app.services.identity import assertion_for_fixture

    return assertion_for_fixture("reviewer.manager@demo.nabd.local")


@pytest.fixture()
def admin_identity():  # type: ignore[no-untyped-def]
    from app.services.identity import assertion_for_fixture

    return assertion_for_fixture("admin.platform@demo.nabd.local")


BENIGN_QUESTION = (
    "What evidence must accompany an internal policy exception request in the Corporate "
    "Services Unit, and who is required to review a Tier 2 request?"
)

VALID_RATIONALE = (
    "Checked each cited passage against the packet claim ledger and recorded this as test "
    "evidence only; no institutional action is authorised by this disposition."
)


@pytest.fixture()
def benign_question() -> str:
    return BENIGN_QUESTION


@pytest.fixture()
def valid_rationale() -> str:
    return VALID_RATIONALE


@pytest.fixture()
def make_case(db: Session):  # type: ignore[no-untyped-def]
    """Create a case row for an identity without processing it."""

    def _make(identity, question: str = BENIGN_QUESTION):  # type: ignore[no-untyped-def]
        from app.domain.ids import new_case_id
        from app.services.fixtures import load_use_case_contract, primary_authorization
        from app.services.orchestrator import build_case_row

        case = build_case_row(
            case_id=new_case_id(),
            identity=identity,
            raw_question=question,
            authorization_id=primary_authorization().authorization_id,
            use_case_contract_id=load_use_case_contract().use_case_contract_id,
        )
        db.add(case)
        db.flush()
        return case

    return _make


@pytest.fixture()
def processed_case(db: Session, make_case, requester_identity):  # type: ignore[no-untyped-def]
    """A benign case processed to ``AWAITING_AUTHORIZED_HUMAN_REVIEW``."""
    from app.services.orchestrator import process_case

    case = make_case(requester_identity)
    result = process_case(db, case, requester_identity)
    return case, result
