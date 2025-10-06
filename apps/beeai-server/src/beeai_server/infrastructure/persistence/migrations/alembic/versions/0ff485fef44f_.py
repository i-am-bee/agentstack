# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""prepare: add user-scoped variables

Revision ID: 0ff485fef44f
Revises: b0388daeb831
Create Date: 2025-09-16 14:18:18.524695

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0ff485fef44f"
down_revision: str | None = "b0388daeb831"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # this needs to be commited first to avoid: unsafe use of new value "user" of enum type envstoreentity
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE envstoreentity ADD VALUE 'user'")


def downgrade() -> None:
    pass
