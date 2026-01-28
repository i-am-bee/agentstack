# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from pathlib import Path

import yaml
from deepagents import SubAgent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from agentstack_sdk.a2a.extensions import LLMFulfillment


@dataclasses.dataclass
class SubAgentConfig:
    name: str
    description: str
    system_prompt: str
    tools: list[BaseTool]
    model: str | None

    def to_deepagent_subagent(self, model: ChatOpenAI) -> SubAgent:
        return SubAgent(
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            tools=self.tools,
            model=model,
        )


def load_subagents(config_path: Path, tools: dict[str, BaseTool]) -> list[SubAgentConfig]:
    """Load subagent definitions from YAML and wire up tools."""

    with open(config_path) as f:
        config = yaml.safe_load(f)

    subagents: list[SubAgentConfig] = []
    for name, spec in config.items():
        subagent = SubAgentConfig(
            name=name,
            description=spec["description"],
            system_prompt=spec["system_prompt"],
            tools=[tools[t] for t in spec["tools"] if t in tools],
            model=spec["model"] if "model" in spec else None,
        )
        subagents.append(subagent)

    return subagents


def create_chat_model(llm_config: LLMFulfillment) -> ChatOpenAI:
    return ChatOpenAI(
        model=llm_config.api_model,
        base_url=llm_config.api_base,
        api_key=SecretStr(llm_config.api_key),
        stream_usage=True,
        # temperature=0,
    )
