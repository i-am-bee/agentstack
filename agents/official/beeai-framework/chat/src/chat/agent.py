# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
import os
from typing import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Part, Role, TaskState, TextPart
from a2a.utils import new_task
from beeai_framework.agents.react import ReActAgent, ReActAgentUpdateEvent
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.backend.chat import ChatModel, ChatModelParameters
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.tool import AnyTool
from beeai_framework.tools.weather.openmeteo import OpenMeteoTool
from openinference.instrumentation.beeai import BeeAIInstrumentor

BeeAIInstrumentor().instrument()
## TODO: https://github.com/phoenixframework/phoenix/issues/6224
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(logging.CRITICAL)


logger = logging.getLogger(__name__)
SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]


def to_framework_messages(history: list[Message]) -> list[UserMessage | AssistantMessage]:
    cur_role = None
    cur_text = ""
    res = []
    for message in history:
        if message.role == Role.agent and message.metadata["update_kind"] != "final_answer":
            continue
        message_text = "".join(part.root.text for part in message.parts if part.root.kind == "text")
        if cur_role != message.role:
            if cur_text:
                res.append(UserMessage(cur_text) if cur_role == Role.user else AssistantMessage(cur_text))
            cur_text = message_text
            cur_role = message.role
        else:
            cur_text += message_text
    if cur_text:
        res.append(UserMessage(cur_text) if cur_role == Role.user else AssistantMessage(cur_text))
    return res


class ChatAgentExecutor(AgentExecutor):
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancelling is not implemented")

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """
        The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
        and weather updates through integrated tools.
        """

        # ensure the model is pulled before running
        os.environ["OPENAI_API_BASE"] = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
        os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "dummy")
        llm = ChatModel.from_name(f"openai:{os.getenv('LLM_MODEL', 'llama3.1')}", ChatModelParameters(temperature=0))

        # Configure tools
        tools: list[AnyTool] = [WikipediaTool(), OpenMeteoTool(), DuckDuckGoSearchTool()]

        # Create agent with memory and tools
        agent = ReActAgent(llm=llm, tools=tools, memory=UnconstrainedMemory())

        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)

        await agent.memory.add_many(to_framework_messages(task.history))
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        try:
            async for data, event in agent.run():
                match (data, event.name):
                    case (ReActAgentUpdateEvent(), "partial_update"):
                        update = data.update.value
                        if not isinstance(update, str):
                            update = update.get_text_content()

                        metadata = {"update_kind": data.update.key}
                        await updater.update_status(
                            state=TaskState.working,
                            message=updater.new_agent_message(
                                parts=[Part(root=TextPart(text=update))], metadata=metadata
                            ),
                        )

        except BaseException as e:
            await updater.failed(message=updater.new_agent_message(parts=[Part(root=TextPart(text=str(e)))]))
            logger.error(f"Agent run failed: {e}")
