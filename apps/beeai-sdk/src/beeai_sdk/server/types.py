# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import TypeAlias

from a2a.types import Artifact, Message, Part, TaskStatus

RunYield: TypeAlias = Message | Part | TaskStatus | Artifact | str | None | Exception
RunYieldResume: TypeAlias = Message | None


class ArtifactChunk(Artifact):
    last_chunk: bool = False
