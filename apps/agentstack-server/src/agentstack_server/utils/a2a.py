# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCard, AgentExtension


def get_extension(agent_card: AgentCard, uri: str) -> AgentExtension | None:
    try:
        extensions = agent_card.capabilities.extensions or []
        return next(ext for ext in extensions if ext.uri == uri)
    except StopIteration:
        return None
