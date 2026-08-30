"""Deterministic PostgreSQL full-text retrieval index over source blocks.

Retrieval is lexical and deterministic: rank descending, then ``excerpt_id`` ascending as
the tie break. The optional vector index stays behind ``ENABLE_VECTOR_RETRIEVAL=false`` and
is not created here, so no deployment can accidentally make it required.

Revision ID: 0003_lexical_retrieval_index
Revises: 0002_append_only_audit
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_lexical_retrieval_index"
down_revision: str | None = "0002_append_only_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    op.execute(
        """
        ALTER TABLE source_blocks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(section_heading, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(text, '')), 'A')
        ) STORED
        """
    )
    op.execute("CREATE INDEX ix_source_blocks_search ON source_blocks USING GIN (search_vector)")


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute("DROP INDEX IF EXISTS ix_source_blocks_search")
    op.execute("ALTER TABLE source_blocks DROP COLUMN IF EXISTS search_vector")
