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

import asyncio
from datetime import timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from tenacity import retry, wait_fixed, stop_after_delay

from beeai_server import logger, get_configuration

migrations_path = Path(__file__).parent.resolve()


@retry(stop=stop_after_delay(timedelta(minutes=10)), wait=wait_fixed(2), reraise=True)
async def _wait_for_db():
    logger.info("Waiting for database to be ready...")
    try:
        db_url = str(get_configuration().persistence.db_url.get_secret_value())
        engine = create_async_engine(db_url)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as e:
        logger.info(f"Error: {e}")
        raise


def migrate(wait_for_db: bool = True):
    from alembic.config import Config
    from alembic import command

    if wait_for_db:
        asyncio.run(_wait_for_db())

    alembic_cfg = Config(migrations_path / "alembic.ini")
    orig_script_location = alembic_cfg.get_main_option("script_location")
    alembic_cfg.set_main_option("script_location", str(migrations_path / orig_script_location))

    command.upgrade(alembic_cfg, "head")


async def create_vector_extension(wait_for_db: bool = True):
    if wait_for_db:
        await _wait_for_db()

    db_url = str(get_configuration().persistence.db_url.get_secret_value())
    engine = create_async_engine(db_url)
    async with engine.connect() as connection, connection.begin() as transaction:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await transaction.commit()
