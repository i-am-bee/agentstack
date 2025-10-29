# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""upgrade procrastinate schema

Revision ID: 327991a3c7a7
Revises: 8b2065340855
Create Date: 2025-07-14 14:21:09.535004

"""

from collections.abc import Sequence

import sqlparse
from alembic import op
from procrastinate.schema import migrations_path

from agentstack_server import get_configuration

# revision identifiers, used by Alembic.
revision: str = "327991a3c7a7"
down_revision: str | None = "8b2065340855"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    migration_3_3_0 = (migrations_path / "03.03.00_01_pre_priority_lock_fetch_job.sql").read_text("utf-8")
    procrastinate_schema = get_configuration().persistence.procrastinate_schema
    op.execute(f"SET search_path TO {procrastinate_schema}")
    for statement in sqlparse.split(migration_3_3_0):
        op.execute(statement)
    op.execute("SET search_path TO public")


def downgrade() -> None:
    """Downgrade schema."""
    raise NotImplementedError("Downgrade not implemented.")
