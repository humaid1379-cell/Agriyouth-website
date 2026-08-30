"""Record the packet hash as sealed at pre-issuance.

A packet carries its confirmed pre-issuance audit reference inside its own sealed preimage.
Attaching a disposition later reseals the packet and changes its current hash, so the hash
that the audit event bound, and that a reviewer disposed of, is retained separately and
never rewritten.

Revision ID: 0004_packet_issued_hash
Revises: 0003_lexical_retrieval_index
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_packet_issued_hash"
down_revision: str | None = "0003_lexical_retrieval_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("decision_packets", sa.Column("issued_sha256", sa.String(length=64), nullable=True))
    op.execute("UPDATE decision_packets SET issued_sha256 = packet_sha256 WHERE issued_sha256 IS NULL")


def downgrade() -> None:
    op.drop_column("decision_packets", "issued_sha256")
