# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""upgrade procrastinate schema

Revision ID: 4fbb7136a125
Revises: d39dd1ff796f
Create Date: 2025-09-11 10:54:42.707325

"""

from collections.abc import Sequence

import sqlparse
from alembic import op
from procrastinate.schema import migrations_path

from agentstack_server import get_configuration

# revision identifiers, used by Alembic.
revision: str = "4fbb7136a125"
down_revision: str | None = "d39dd1ff796f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    migration_3_4_0_pre = (migrations_path / "03.04.00_01_pre_add_retry_failed_job_procedure.sql").read_text("utf-8")
    migration_3_4_0_post = (migrations_path / "03.04.00_50_post_add_retry_failed_job_procedure.sql").read_text("utf-8")
    procrastinate_schema = get_configuration().persistence.procrastinate_schema
    op.execute(f"SET search_path TO {procrastinate_schema}")
    for statement in sqlparse.split(migration_3_4_0_pre):
        op.execute(statement)
    for statement in sqlparse.split(migration_3_4_0_post):
        op.execute(statement)
    op.execute("SET search_path TO public")


def downgrade() -> None:
    """Downgrade schema."""
    raise NotImplementedError("Downgrade not implemented.")
