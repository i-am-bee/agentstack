# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from pydantic import AwareDatetime, BaseModel


class A2ARequestTask(BaseModel):
    task_id: str
    created_by: UUID
    provider_id: UUID
    created_at: AwareDatetime
    last_accessed_at: AwareDatetime