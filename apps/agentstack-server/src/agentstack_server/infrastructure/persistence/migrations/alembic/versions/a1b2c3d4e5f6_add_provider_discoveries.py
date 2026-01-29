# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


"""add provider_discoveries table

Revision ID: a1b2c3d4e5f6
Revises: fb04d94673c6
Create Date: 2026-01-23 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "109a6afdf170"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

discovery_state_enum = sa.Enum("pending", "in_progress", "completed", "failed", name="discoverystate")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(  # pyright: ignore[reportUnusedCallResult]
        "provider_discoveries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("docker_image", sa.String(2048), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("agent_card", JSONB(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    discovery_state_enum.create(op.get_bind())
    op.add_column("provider_discoveries", sa.Column("status", discovery_state_enum, nullable=False))

    op.create_index("ix_provider_discoveries_created_at", "provider_discoveries", ["created_at"])
    op.create_index("ix_provider_discoveries_created_by", "provider_discoveries", ["created_by"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_provider_discoveries_created_by", "provider_discoveries")
    op.drop_index("ix_provider_discoveries_created_at", "provider_discoveries")
    op.drop_table("provider_discoveries")
    discovery_state_enum.drop(op.get_bind())
