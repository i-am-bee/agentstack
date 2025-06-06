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

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr, AwareDatetime

from beeai_server.utils.utils import utc_now


class UserRole(StrEnum):
    admin = "admin"
    user = "user"


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: UserRole = UserRole.user
    email: EmailStr
    created_at: AwareDatetime = Field(default_factory=utc_now)
