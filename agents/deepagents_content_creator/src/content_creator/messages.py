# © Copyright IBM Corporation 2025
# SPDX-License-Identifier: Apache-2.0


import itertools

from a2a.types import Role
from a2a.types import Message as A2AMessage
from langchain.messages import AIMessage, HumanMessage


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
