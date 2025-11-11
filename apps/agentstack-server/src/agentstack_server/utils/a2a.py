# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from a2a.types import AgentCard, AgentExtension
from pydantic import BaseModel


class FieldChange(BaseModel):
    old: Any
    new: Any


def get_extension(agent_card: AgentCard, uri: str) -> AgentExtension | None:
    try:
        extensions = agent_card.capabilities.extensions or []
        return next(ext for ext in extensions if ext.uri == uri)
    except StopIteration:
        return None


def detect_card_changes(old_card: AgentCard, new_card: AgentCard) -> dict[str, FieldChange]:
    """Detect specific changes between two agent cards."""
    old_dict = old_card.model_dump(mode="json", exclude={"signatures"})
    new_dict = new_card.model_dump(mode="json", exclude={"signatures"})

    changes = {}
    all_keys = set(old_dict.keys()) | set(new_dict.keys())

    for key in all_keys:
        old_val = old_dict.get(key)
        new_val = new_dict.get(key)
        if old_val != new_val:
            changes[key] = FieldChange(old=old_val, new=new_val)

    return changes
