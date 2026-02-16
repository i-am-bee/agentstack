# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from pathlib import Path
import itertools
import yaml
from deepagents import SubAgent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from a2a.types import Role
from a2a.types import Message as A2AMessage
from langchain.messages import AIMessage, HumanMessage
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


ROLE_TO_MESSAGE: dict[Role, type[HumanMessage] | type[AIMessage]] = {
    Role.user: HumanMessage,
    Role.agent: AIMessage,
}


def to_langchain_messages(history: list[A2AMessage]) -> list[AIMessage | HumanMessage]:
    if not history:
        return []

    langchain_messages: list[AIMessage | HumanMessage] = []

    for role, group in itertools.groupby(history, key=lambda msg: msg.role):
        # Collect all text parts from consecutive messages with the same role
        text_parts: list[str] = []
        for message in group:
            text_parts.extend(part.root.text for part in message.parts if part.root.kind == "text")

        # Join all text parts and create the appropriate message type
        combined_text: str = "".join(text_parts)

        if role not in ROLE_TO_MESSAGE:
            raise ValueError(f"Unknown role in message history: {role}")

        message_class: type[HumanMessage] | type[AIMessage] = ROLE_TO_MESSAGE[role]
        langchain_messages.append(message_class(content=combined_text))

    return langchain_messages
