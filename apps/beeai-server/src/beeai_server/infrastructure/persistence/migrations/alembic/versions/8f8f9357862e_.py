# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""add version info and unmanaged state to provieders

Revision ID: 8f8f9357862e
Revises: 2626892a4e65
Create Date: 2025-10-14 15:32:31.222401

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f8f9357862e"
down_revision: str | None = "2626892a4e65"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

provider_type_enum = sa.Enum("managed", "unmanaged", name="providertype")
unmanaged_state_enum = sa.Enum("online", "offline", name="unmanagedstate")


def upgrade() -> None:
    """Upgrade schema."""
    provider_type_enum.create(op.get_bind())
    unmanaged_state_enum.create(op.get_bind())

    # Step 1: Add type column as nullable
    op.add_column("providers", sa.Column("type", provider_type_enum, nullable=True))

    # Step 2: Fill the type column based on source
    op.execute(
        """
        UPDATE providers
        SET type = CASE
                       WHEN source LIKE 'http%' THEN 'unmanaged'::providertype
                       ELSE 'managed'::providertype
            END
        """
    )

    # Step 3: Make type column non-nullable
    op.alter_column("providers", "type", nullable=False)

    op.add_column(
        "providers",
        sa.Column("version_info", sa.JSON(), server_default='{"docker": null, "github": null}', nullable=False),
    )

    op.add_column("providers", sa.Column("unmanaged_state", unmanaged_state_enum, nullable=True))

    op.execute("""
        UPDATE providers
        SET unmanaged_state = 'offline'::unmanagedstate
        WHERE type = 'unmanaged'::providertype
    """)

    op.drop_column("providers", "auto_remove")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "providers",
        sa.Column("auto_remove", sa.BOOLEAN(), autoincrement=False, server_default="false", nullable=False),
    )
    op.drop_column("providers", "unmanaged_state")
    op.drop_column("providers", "version_info")
    op.drop_column("providers", "type")
    provider_type_enum.drop(op.get_bind())
    unmanaged_state_enum.drop(op.get_bind())
    # ### end Alembic commands ###
