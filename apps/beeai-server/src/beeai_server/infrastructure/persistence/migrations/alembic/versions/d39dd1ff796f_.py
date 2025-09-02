# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""provider upgrading

Revision ID: d39dd1ff796f
Revises: 46ec8881ac4c
Create Date: 2025-09-02 13:32:03.928711

"""

import hashlib
from collections.abc import Sequence
from contextlib import contextmanager
from uuid import UUID

import sqlalchemy as sa
from alembic import op

from beeai_server.utils.docker import DockerImageID

# revision identifiers, used by Alembic.
revision: str = "d39dd1ff796f"
down_revision: str | None = "46ec8881ac4c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def get_old_provider_id(source: str) -> UUID:
    """Calculate provider ID using the old hash method (entire source string)."""
    location_digest = hashlib.sha256(source.encode()).digest()
    return UUID(bytes=location_digest[:16])


def get_new_provider_id(source: str) -> UUID:
    """Calculate provider ID using the new hash method (registry/repository only)."""
    docker_image = DockerImageID(root=source)
    location_digest = hashlib.sha256(docker_image.base.encode()).digest()
    return UUID(bytes=location_digest[:16])


@contextmanager
def _temporarily_disable_fkeys():
    op.drop_constraint("user_feedback_provider_id_fkey", "user_feedback", type_="foreignkey")
    op.drop_constraint("variables_provider_id_fkey", "variables", type_="foreignkey")

    yield

    op.create_foreign_key(
        "variables_provider_id_fkey",
        "variables",
        referent_table="providers",
        local_cols=["provider_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "user_feedback_provider_id_fkey",
        "user_feedback",
        referent_table="providers",
        local_cols=["provider_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def upgrade() -> None:
    """Upgrade schema."""
    with _temporarily_disable_fkeys():
        op.alter_column("providers", "auto_stop_timeout_sec", existing_type=sa.INTEGER(), nullable=True)
        # ### end Alembic commands ###

        # Update provider IDs for docker images using deferred constraints
        connection = op.get_bind()

        # Get all providers and collect ID mappings
        result = connection.execute(sa.text("SELECT id, source FROM providers"))
        providers = result.fetchall()

        id_mappings = {}
        for provider in providers:
            old_id = provider[0]
            source = provider[1]

            try:
                DockerImageID(root=source)
                new_id = get_new_provider_id(source)

                # Only update if the ID actually changed
                if str(old_id) != str(new_id):
                    id_mappings[str(old_id)] = str(new_id)
            except (ValueError, Exception):
                # Skip non-docker images or invalid formats
                continue

        # Update all references atomically - order doesn't matter with deferred constraints
        for old_id, new_id in id_mappings.items():
            # Update providers table
            connection.execute(
                sa.text("UPDATE providers SET id = :new_id WHERE id = :old_id"), {"new_id": new_id, "old_id": old_id}
            )

            # Update foreign key references
            connection.execute(
                sa.text("UPDATE variables SET provider_id = :new_id WHERE provider_id = :old_id"),
                {"new_id": new_id, "old_id": old_id},
            )

            connection.execute(
                sa.text("UPDATE user_feedback SET provider_id = :new_id WHERE provider_id = :old_id"),
                {"new_id": new_id, "old_id": old_id},
            )


def downgrade() -> None:
    """Downgrade schema."""
    with _temporarily_disable_fkeys():
        op.alter_column("providers", "auto_stop_timeout_sec", existing_type=sa.INTEGER(), nullable=False)
        # ### end Alembic commands ###

        # Reverse the provider ID changes using deferred constraints
        connection = op.get_bind()

        # Get all providers and collect ID mappings for reversal
        result = connection.execute(sa.text("SELECT id, source FROM providers"))
        providers = result.fetchall()

        id_mappings = {}
        for provider in providers:
            current_id = provider[0]
            source = provider[1]

            try:
                DockerImageID(root=source)
                old_id = get_old_provider_id(source)

                # Only update if the ID actually changed
                if str(current_id) != str(old_id):
                    id_mappings[str(current_id)] = str(old_id)
            except (ValueError, Exception):
                # Skip non-docker images or invalid formats
                continue

        # Update all references atomically - order doesn't matter with deferred constraints
        for current_id, old_id in id_mappings.items():
            # Update providers table
            connection.execute(
                sa.text("UPDATE providers SET id = :old_id WHERE id = :current_id"),
                {"old_id": old_id, "current_id": current_id},
            )

            # Update foreign key references
            connection.execute(
                sa.text("UPDATE variables SET provider_id = :old_id WHERE provider_id = :current_id"),
                {"old_id": old_id, "current_id": current_id},
            )

            connection.execute(
                sa.text("UPDATE user_feedback SET provider_id = :old_id WHERE provider_id = :current_id"),
                {"old_id": old_id, "current_id": current_id},
            )
