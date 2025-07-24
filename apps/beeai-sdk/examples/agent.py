# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import collections
import os
import textwrap
import typing

import a2a.server.agent_execution
import a2a.server.apps
import a2a.server.events
import a2a.server.request_handlers
import a2a.server.tasks
import a2a.types
import a2a.utils
import beeai_framework.adapters.openai.backend.chat
import beeai_framework.agents.react
import beeai_framework.backend
import beeai_framework.memory
import beeai_framework.tools.search.duckduckgo
import beeai_framework.tools.search.wikipedia
import beeai_framework.tools.weather.openmeteo
import uvicorn

import beeai_sdk.a2a_extensions

agent_details_extension = beeai_sdk.a2a_extensions.AgentDetailsExtension(
    params=beeai_sdk.a2a_extensions.AgentDetails(
        ui_type="chat",
    )
)

llm_service_extension = beeai_sdk.a2a_extensions.LLMServiceExtension(
    params=beeai_sdk.a2a_extensions.services.llm.LLMServiceExtensionParams(
        llm_demands={
            "default": beeai_sdk.a2a_extensions.LLMDemand(
                description="Default LLM for the agent", suggested=("openai/gpt-4o", "ollama/granite3.3:8b")
            )
        }
    ),
)


class ChatAgentExecutor(a2a.server.agent_execution.AgentExecutor):
    def __init__(self):
        super().__init__()
        self.context_memory: collections.defaultdict[str, beeai_framework.memory.UnconstrainedMemory] = (
            collections.defaultdict(beeai_framework.memory.UnconstrainedMemory)
        )
        self.context_llm: dict[str, dict[str, beeai_sdk.a2a_extensions.services.llm.LLMFulfillment]] = {}

    @typing.override
    async def cancel(
        self, context: a2a.server.agent_execution.RequestContext, event_queue: a2a.server.events.EventQueue
    ) -> None:
        raise NotImplementedError("Cancelling is not implemented")

    @typing.override
    async def execute(
        self, context: a2a.server.agent_execution.RequestContext, event_queue: a2a.server.events.EventQueue
    ):
        if not context.message or not context.context_id:
            raise ValueError("Context must have a message and context_id")

        llm_metadata = llm_service_extension.parse_message_metadata(context.message)
        if llm_metadata:
            self.context_llm[context.context_id] = llm_metadata.llm_fulfillments

        if self.context_llm.get(context.context_id) is None:
            raise ValueError("No LLM configured!")

        agent = beeai_framework.agents.react.ReActAgent(
            llm=beeai_framework.adapters.openai.backend.chat.OpenAIChatModel(
                model_id=self.context_llm[context.context_id]["default"].api_model,
                api_key=self.context_llm[context.context_id]["default"].api_key,
                base_url=self.context_llm[context.context_id]["default"].api_base,
            ),
            tools=[
                beeai_framework.tools.search.wikipedia.WikipediaTool(),
                beeai_framework.tools.weather.openmeteo.OpenMeteoTool(),
                beeai_framework.tools.search.duckduckgo.DuckDuckGoSearchTool(),
            ],
            memory=self.context_memory[context.context_id],
        )

        await self.context_memory[context.context_id].add(beeai_framework.backend.UserMessage(context.get_user_input()))

        context.current_task = a2a.utils.new_task(context.message)
        assert context.task_id is not None
        updater = a2a.server.tasks.TaskUpdater(event_queue, context.task_id, context.context_id)
        try:
            final_answer = ""
            async for data, event in agent.run():
                match (data, event.name):
                    case (beeai_framework.agents.react.ReActAgentUpdateEvent(), "partial_update"):
                        update = data.update.value
                        if not isinstance(update, str):
                            update = update.get_text_content()

                        if data.update.key == "final_answer":
                            final_answer += update
                            await updater.update_status(
                                state=a2a.types.TaskState.working,
                                message=updater.new_agent_message(
                                    parts=[a2a.types.Part(root=a2a.types.TextPart(text=update))]
                                ),
                            )
            await self.context_memory[context.context_id].add(beeai_framework.backend.AssistantMessage(final_answer))
            await updater.complete()
        except BaseException as e:
            await updater.failed(
                message=updater.new_agent_message(parts=[a2a.types.Part(root=a2a.types.TextPart(text=str(e)))])
            )
            raise


async def serve():
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "10000"))
    await uvicorn.Server(
        uvicorn.Config(
            app=a2a.server.apps.A2AStarletteApplication(
                agent_card=a2a.types.AgentCard(
                    name="Chat Agent",
                    description=textwrap.dedent(
                        """\
                        The agent is an AI-powered conversational system designed to process user messages, maintain context,
                        and generate intelligent responses. Built on the **BeeAI framework**, it leverages memory and external
                        tools to enhance interactions. It supports real-time web search, Wikipedia lookups, and weather updates,
                        making it a versatile assistant for various applications.
                        ## How It Works
                        The agent processes incoming messages and maintains a conversation history using an **unconstrained
                        memory module**. It utilizes a language model (`CHAT_MODEL`) to generate responses and can optionally
                        integrate external tools for additional functionality.
                        It supports:
                        - **Web Search (DuckDuckGo)** - Retrieves real-time search results.
                        - **Wikipedia Search** - Fetches summaries from Wikipedia.
                        - **Weather Information (OpenMeteo)** - Provides real-time weather updates.
                        The agent also includes an **event-based streaming mechanism**, allowing it to send partial responses
                        to clients as they are generated.
                        ## Key Features
                        - **Conversational AI** - Handles multi-turn conversations with memory.
                        - **Tool Integration** - Supports real-time search, Wikipedia lookups, and weather updates.
                        - **Event-Based Streaming** - Can send partial updates to clients as responses are generated.
                        - **Customizable Configuration** - Users can enable or disable specific tools for enhanced responses.
                        """
                    ),
                    documentation_url="https://github.com/i-am-bee/beeai-platform/blob/main/agents/official/beeai-framework/chat",
                    url=f"http://{host}:{port}/",
                    version="1.0.0",
                    default_input_modes=["text", "text/plain"],
                    default_output_modes=["text", "text/plain"],
                    capabilities=a2a.types.AgentCapabilities(
                        streaming=True,
                        push_notifications=False,
                        state_transition_history=False,
                        extensions=[*llm_service_extension.to_agent_card_extensions(required=True)],
                    ),
                    skills=[
                        a2a.types.AgentSkill(
                            id="chat",
                            name="Chat",
                            description="Answer complex questions using web search sources",
                            tags=["chat"],
                            examples=["What's the current weather in the birth town of Michael Jackson?"],
                        )
                    ],
                ),
                http_handler=a2a.server.request_handlers.DefaultRequestHandler(
                    agent_executor=ChatAgentExecutor(), task_store=a2a.server.tasks.InMemoryTaskStore()
                ),
            ).build(),
            host=host,
            port=port,
            log_level="info",
        )
    ).serve()


if __name__ == "__main__":
    asyncio.run(serve())
