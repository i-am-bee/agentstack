# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from enum import Enum
from typing import Final, Literal, TypeAlias

DOCKER_MANIFEST_LABEL_NAME: Final[str] = "beeai.dev.agent.json"


class _Undefined(Enum):
    undefined = "undefined"


undefined = _Undefined.undefined
Undefined: TypeAlias = Literal[_Undefined.undefined]  # noqa: UP040

DEFAULT_AUTO_STOP_TIMEOUT: Final[timedelta] = timedelta(minutes=20)

# A2A platform constants
AGENT_DETAIL_EXTENSION_URI: Final[str] = "https://a2a-extensions.beeai.dev/ui/agent-detail/v1"
SELF_REGISTRATION_EXTENSION_URI: Final[str] = "https://a2a-extensions.beeai.dev/services/platform-self-registration/v1"

MODEL_API_KEY_SECRET_NAME = "MODEL_API_KEY"
