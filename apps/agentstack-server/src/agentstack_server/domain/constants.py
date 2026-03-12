# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum
from typing import Final, Literal, TypeAlias


class _Undefined(Enum):
    undefined = "undefined"


undefined = _Undefined.undefined
Undefined: TypeAlias = Literal[_Undefined.undefined]  # noqa: UP040

# A2A platform constants
AGENT_DETAIL_EXTENSION_URI: Final[str] = "https://a2a-extensions.agentstack.beeai.dev/ui/agent-detail/v1"
SELF_REGISTRATION_EXTENSION_URI: Final[str] = (
    "https://a2a-extensions.agentstack.beeai.dev/services/platform-self-registration/v1"
)

MODEL_API_KEY_SECRET_NAME = "MODEL_API_KEY"
