# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""empty message

Revision ID: be5ec6ff3271
Revises: 48ffed989775
Create Date: 2025-06-17 12:58:21.414385

"""

from typing import Sequence, Union

from alembic import op

from beeai_server import get_configuration

# revision identifiers, used by Alembic.
revision: str = "be5ec6ff3271"
down_revision: Union[str, None] = "48ffed989775"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
    op.execute(f"DROP SCHEMA IF EXISTS {get_configuration().persistence.vector_db_schema}")

    # We are not dropping the extension (user might have insufficient permissions)
