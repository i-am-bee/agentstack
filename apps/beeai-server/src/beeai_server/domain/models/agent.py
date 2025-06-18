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

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, AwareDatetime

from acp_sdk.models import AgentManifest as AcpAgentOriginal, Metadata as AcpMetadataOriginal

from beeai_server.utils.utils import utc_now


class EnvVar(BaseModel):
    name: str
    description: str | None = None
    required: bool = False


class AcpMetadata(AcpMetadataOriginal):
    env: list[EnvVar] = Field(default_factory=list, description="For configuration -- passed to the process")
    ui: dict[str, Any] | None = None
    provider_id: UUID


class Agent(AcpAgentOriginal, extra="allow"):
    id: UUID = Field(default_factory=uuid4)
    metadata: AcpMetadata

    @property
    def provider_id(self):
        return self.metadata.provider_id


class AgentRunRequest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    acp_run_id: UUID | None = None
    agent_id: UUID
    created_at: AwareDatetime = Field(default_factory=utc_now)
    finished_at: AwareDatetime | None = None
    created_by: UUID

    def set_finished(self):
        self.finished_at = utc_now()
