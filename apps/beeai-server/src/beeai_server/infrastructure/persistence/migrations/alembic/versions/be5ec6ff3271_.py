# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""empty message

Revision ID: be5ec6ff3271
Revises: 48ffed989775
Create Date: 2025-06-17 12:58:21.414385

"""

from collections.abc import Sequence

from alembic import op

from beeai_server import get_configuration

# revision identifiers, used by Alembic.
revision: str = "be5ec6ff3271"
down_revision: str | None = "48ffed989775"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create pgvector extension
    # This will fail if the user is not a superuser and the extension does not exist yet
    # It will pass if the extension already exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Create separate schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {get_configuration().persistence.vector_db_schema}")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop vector_db schema
    op.execute(f"DROP SCHEMA IF EXISTS {get_configuration().persistence.vector_db_schema} CASCADE")

    # We are not dropping the extension (user might have insufficient permissions)
