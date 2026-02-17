# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from agentstack_sdk.server import Server
from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.server.context import RunContext

from agentstack_sdk.a2a.extensions import (
    LLMServiceExtensionSpec,
    LLMServiceExtensionServer,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
    AgentDetail,
)

server = Server()


class State(TypedDict):
    messages: Annotated[list, add_messages]


@server.agent(
    name="Reflection Agent",
    description="Reflection agent that writes essays and reflects on them",
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="Hello! I am your essay assistant. What would you like me to write about today?",
        input_placeholder="Enter your essay topic or request here...",
    ),
)
async def reflection_agent(
    input: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    llm_service: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(
            suggested=(
                "ollama:llama3.1:8b",
                "openai:gpt-4o",
            )
        ),
    ],
):
    if llm_service and llm_service.data and llm_service.data.llm_fulfillments:
        llm_config = llm_service.data.llm_fulfillments.get("default")
    else:
        raise ValueError("No LLM configuration provided")

    llm = ChatOpenAI(
        model=llm_config.api_model,
        api_key=llm_config.api_key,
        base_url=llm_config.api_base,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an essay assistant tasked with writing excellent 5-paragraph essays."
                " Generate the best essay possible for the user's request."
                " If the user provides critique, respond with a revised version of your previous attempts.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    generate = prompt | llm

    reflection_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a teacher grading an essay submission. Generate critique and recommendations for the user's submission."
                " Provide detailed recommendations, including requests for length, depth, style, etc.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    reflect = reflection_prompt | llm

    async def generation_node(state: State) -> State:
        return {"messages": [await generate.ainvoke(state["messages"])]}

    async def reflection_node(state: State) -> State:
        cls_map = {"ai": HumanMessage, "human": AIMessage}
        translated = [state["messages"][0]] + [cls_map[msg.type](content=msg.content) for msg in state["messages"][1:]]
        res = await reflect.ainvoke(translated)
        return {"messages": [HumanMessage(content=res.content)]}

    def should_continue(state: State):
        if len(state["messages"]) > 6:
            return END
        return "reflect"

    builder = StateGraph(State)
    builder.add_node("generate", generation_node)
    builder.add_node("reflect", reflection_node)
    builder.add_edge(START, "generate")
    builder.add_conditional_edges("generate", should_continue)
    builder.add_edge("reflect", "generate")

    memory = InMemorySaver()
    graph = builder.compile(checkpointer=memory)
    config = {"configurable": {"thread_id": "1"}}

    user_input = get_message_text(input)

    events = graph.astream(
        {
            "messages": [HumanMessage(content=user_input)],
        },
        config,
    )

    async for event in events:
        for node_name, output in event.items():
            if "messages" in output:
                last_msg = output["messages"][-1]
                yield trajectory.trajectory_metadata(
                    title=node_name,
                    content=last_msg.content,
                )
            else:
                yield trajectory.trajectory_metadata(title=node_name, content=str(output))

    # After the loop finishes, we might want to yield the final essay as the result
    state = await graph.aget_state(config)
    final_essay = state.values["messages"][-1].content
    yield final_essay


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
