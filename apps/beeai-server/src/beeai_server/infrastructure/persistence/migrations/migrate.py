# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from tenacity import retry, stop_after_delay, wait_fixed

from beeai_server import get_configuration, logger

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
    from alembic import command
    from alembic.config import Config

    if wait_for_db:
        asyncio.run(_wait_for_db())

    alembic_cfg = Config(migrations_path / "alembic.ini")
    orig_script_location = alembic_cfg.get_main_option("script_location")
    alembic_cfg.set_main_option("script_location", str(migrations_path / orig_script_location))

    command.upgrade(alembic_cfg, "head")


async def create_vector_extension(wait_for_db: bool = True):
    if wait_for_db:
        await _wait_for_db()

    engine = get_configuration().persistence.create_async_engine()
    async with engine.connect() as connection, connection.begin() as transaction:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.execute(text("SET maintenance_work_mem = '512MB'"))

        # Improve recall at the cost of performance
        # In pgvector when using filtering (which we are doing heavily - by the vector_store_id column)
        # it might actually return fewer results than it should because filtering is applied after the index is scanned
        # to mitigate this we use the iterative scan feature
        # - filtering: https://github.com/pgvector/pgvector?tab=readme-ov-file#filtering
        # - iterative index scan: https://github.com/pgvector/pgvector?tab=readme-ov-file#iterative-index-scans
        await connection.execute(text("SET hnsw.ef_search = 1000"))
        await connection.execute(text("SET hnsw.iterative_scan = strict_order"))
        await connection.execute(text("SET hnsw.max_scan_tuples = 1000000"))  # 1M, default is 20k
        await transaction.commit()
