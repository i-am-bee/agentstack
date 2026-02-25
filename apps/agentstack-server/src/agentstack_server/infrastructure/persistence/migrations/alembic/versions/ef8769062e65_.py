# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

"""migrate extracted_file_id to junction table

Revision ID: ef8769062e65
Revises: 15e0c8efe77f
Create Date: 2025-11-30 21:18:30.961482

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef8769062e65"
down_revision: str | None = "15e0c8efe77f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create junction table for extraction_files with format column
    op.create_table(
        "extraction_files",
        sa.Column("extraction_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.Column("format", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["extraction_id"], ["text_extractions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("extraction_id", "format", name="uq_extraction_files_extraction_id_format"),
    )

    # Migrate existing data from extracted_file_id to junction table
    # Infer format from content_type: markdown for text/markdown, vendor_specific_json for application/json
    # Only migrate non-null extracted_file_id values
    op.execute("""
        INSERT INTO extraction_files (extraction_id, file_id, format)
        SELECT
            te.id,
            te.extracted_file_id,
            CASE
                WHEN f.content_type = 'text/markdown' THEN 'markdown'
                WHEN f.content_type = 'application/json' THEN 'vendor_specific_json'
                ELSE NULL
            END
        FROM text_extractions te
        JOIN files f ON te.extracted_file_id = f.id
        WHERE te.extracted_file_id IS NOT NULL
    """)

    # Drop the old extracted_file_id column
    op.drop_constraint(op.f("text_extractions_extracted_file_id_fkey"), "text_extractions", type_="foreignkey")
    op.drop_column("text_extractions", "extracted_file_id")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the extracted_file_id column
    op.add_column(
        "text_extractions",
        sa.Column("extracted_file_id", sa.UUID(), autoincrement=False, nullable=True),
    )

    # Migrate data back from junction table to extracted_file_id
    # Only keep markdown files, delete other files
    op.execute("""
        UPDATE text_extractions te
        SET extracted_file_id = ef.file_id
        FROM (
            SELECT DISTINCT ON (ef.extraction_id) ef.extraction_id, ef.file_id
            FROM extraction_files ef
            JOIN files f ON ef.file_id = f.id
            WHERE f.content_type = 'text/markdown'
            ORDER BY ef.extraction_id
        ) ef
        WHERE te.id = ef.extraction_id
    """)

    # Delete non-markdown extracted files (except those with "in-place" backend)
    op.execute("""
        DELETE FROM files
        WHERE id IN (
            SELECT ef.file_id
            FROM extraction_files ef
            JOIN files f ON ef.file_id = f.id
            JOIN text_extractions te ON ef.extraction_id = te.id
            WHERE f.content_type != 'text/markdown'
            AND (te.extraction_metadata->>'backend') != 'in-place'
        )
    """)

    # Add the foreign key constraint
    op.create_foreign_key(
        op.f("text_extractions_extracted_file_id_fkey"),
        "text_extractions",
        "files",
        ["extracted_file_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Drop the junction table
    op.drop_table("extraction_files")
