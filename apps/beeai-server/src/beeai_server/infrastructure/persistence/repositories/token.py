# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
from kink import inject
from sqlalchemy import Column, DateTime, String, Table, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.configuration import Configuration
from beeai_server.domain.repositories.token import ITokenPasscodeRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

token_table = Table(
    "token",
    metadata,
    Column("passcode", String(256), primary_key=True),
    Column("token", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=datetime.now(UTC)),
)


@inject
class SqlAlchemyTokenPasscodeRepository(ITokenPasscodeRepository):
    def __init__(self, connection: AsyncConnection, configuration: Configuration):
        self.connection = connection
        if not configuration.persistence.encryption_key:
            raise RuntimeError("Missing encryption key in configuration.")

        self.fernet = Fernet(configuration.persistence.encryption_key.get_secret_value())
        self.ttl_seconds = configuration.oidc.passcode_ttl_seconds

    async def set(self, passcode: str, token: dict) -> None:
        token_str = json.dumps(token)
        encrypted_token = self.fernet.encrypt(token_str.encode()).decode()
        now = datetime.now(UTC)

        # First try to update
        update_stmt = (
            token_table.update().where(token_table.c.passcode == passcode).values(token=encrypted_token, created_at=now)
        )
        result = await self.connection.execute(update_stmt)

        if result.rowcount == 0:
            # If nothing was updated, insert instead
            insert_stmt = token_table.insert().values(passcode=passcode, token=encrypted_token, created_at=now)
            await self.connection.execute(insert_stmt)

    async def get(self, passcode: str, default: str | None = None) -> dict:
        now = datetime.now(UTC)

        query = (
            select(token_table)
            .where(token_table.c.passcode == passcode)
            .where(token_table.c.created_at >= now - timedelta(seconds=self.ttl_seconds))
        )
        result = await self.connection.execute(query)
        row = result.fetchone()
        if not row:
            if default is None:
                raise EntityNotFoundError(entity="token_passcode", id=passcode)
            return default
        decrypted_token_str = self.fernet.decrypt(row.token.encode()).decode()
        return json.loads(decrypted_token_str)

    async def delete(self, passcode: str) -> None:
        await self.connection.execute(delete(token_table).where(token_table.c.passcode == passcode))

    async def delete_expired(self) -> None:
        expiry_cutoff = datetime.now(UTC) - timedelta(seconds=self.ttl_seconds)
        result = await self.connection.execute(delete(token_table).where(token_table.c.created_at < expiry_cutoff))
        return result.rowcount
