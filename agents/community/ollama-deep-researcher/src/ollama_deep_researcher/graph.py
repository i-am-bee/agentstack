# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json

from typing_extensions import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph

from ollama_deep_researcher.configuration import Configuration, SearchAPI
from ollama_deep_researcher.utils import (
    deduplicate_and_format_sources,
    tavily_search,
    format_sources,
    perplexity_search,
    duckduckgo_search,
)
from ollama_deep_researcher.state import SummaryState, SummaryStateInput, SummaryStateOutput
from ollama_deep_researcher.prompts import query_writer_instructions, summarizer_instructions, reflection_instructions

config = Configuration()


# Nodes
def generate_query(state: SummaryState):
    """Generate a query for web search"""

    # Format the prompt
    query_writer_instructions_formatted = query_writer_instructions.format(research_topic=state.research_topic)

    # Generate a query
    llm_json_mode = ChatOpenAI(
        model=config.llm_model,
        openai_api_key=config.llm_api_key,
        openai_api_base=config.llm_api_base,
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    result = llm_json_mode.invoke(
        [
            SystemMessage(content=query_writer_instructions_formatted),
            HumanMessage(content="Generate a query for web search:"),
        ]
    )
    query = json.loads(result.content)

    return {"search_query": query["query"]}


def web_research(state: SummaryState):
    """Gather information from the web"""

    # Search the web
    if config.search_api == SearchAPI.TAVILY:
        search_results = tavily_search(state.search_query, include_raw_content=True, max_results=1)
        search_str = deduplicate_and_format_sources(
            search_results, max_tokens_per_source=1000, include_raw_content=True
        )
    elif config.search_api == SearchAPI.PERPLEXITY:
        search_results = perplexity_search(state.search_query, state.research_loop_count)
        search_str = deduplicate_and_format_sources(
            search_results, max_tokens_per_source=1000, include_raw_content=False
        )
    elif config.search_api == SearchAPI.DUCKDUCKGO:
        search_results = duckduckgo_search(state.search_query, max_results=3, fetch_full_page=config.fetch_full_page)
        search_str = deduplicate_and_format_sources(
            search_results, max_tokens_per_source=1000, include_raw_content=True
        )
    else:
        raise ValueError(f"Unsupported search API: {config.search_api}")

    return {
        "sources_gathered": [format_sources(search_results)],
        "research_loop_count": state.research_loop_count + 1,
        "web_research_results": [search_str],
    }


def summarize_sources(state: SummaryState):
    """Summarize the gathered sources"""

    # Existing summary
    existing_summary = state.running_summary

    # Most recent web research
    most_recent_web_research = state.web_research_results[-1]

    # Build the human message
    if existing_summary:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Search Results> \n {most_recent_web_research} \n <New Search Results>"
        )
    else:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Search Results> \n {most_recent_web_research} \n <Search Results>"
        )

    # Run the LLM
    llm = ChatOpenAI(
        model=config.llm_model,
        openai_api_key=config.llm_api_key,
        openai_api_base=config.llm_api_base,
        temperature=0,
    )
    result = llm.invoke([SystemMessage(content=summarizer_instructions), HumanMessage(content=human_message_content)])

    running_summary = result.content

    # TODO: This is a hack to remove the <think> tags w/ Deepseek models
    # It appears very challenging to prompt them out of the responses
    while "<think>" in running_summary and "</think>" in running_summary:
        start = running_summary.find("<think>")
        end = running_summary.find("</think>") + len("</think>")
        running_summary = running_summary[:start] + running_summary[end:]

    return {"running_summary": running_summary}


def reflect_on_summary(state: SummaryState):
    """Reflect on the summary and generate a follow-up query"""

    # Generate a query
    llm_json_mode = ChatOpenAI(
        model=config.llm_model,
        openai_api_key=config.llm_api_key,
        openai_api_base=config.llm_api_base,
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    result = llm_json_mode.invoke(
        [
            SystemMessage(content=reflection_instructions.format(research_topic=state.research_topic)),
            HumanMessage(
                content=f"Identify a knowledge gap and generate a follow-up web search query based on our existing knowledge: {state.running_summary}"
            ),
        ]
    )
    follow_up_query = json.loads(result.content)

    # Get the follow-up query
    query = follow_up_query.get("follow_up_query")

    # JSON mode can fail in some cases
    if not query:
        # Fallback to a placeholder query
        return {"search_query": f"Tell me more about {state.research_topic}"}


def finalize_summary(state: SummaryState):
    """Finalize the summary"""

    # Format all accumulated sources into a single bulleted list
    all_sources = "\n".join(source for source in state.sources_gathered)
    state.running_summary = f"## Summary\n\n{state.running_summary}\n\n ### Sources:\n{all_sources}"
    return {"running_summary": state.running_summary}


def route_research(state: SummaryState) -> Literal["finalize_summary", "web_research"]:
    """Route the research based on the follow-up query"""

    if state.research_loop_count <= config.max_web_research_loops:
        return "web_research"
    else:
        return "finalize_summary"


# Add nodes and edges
builder = StateGraph(SummaryState, input=SummaryStateInput, output=SummaryStateOutput)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("summarize_sources", summarize_sources)
builder.add_node("reflect_on_summary", reflect_on_summary)
builder.add_node("finalize_summary", finalize_summary)

# Add edges
builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "web_research")
builder.add_edge("web_research", "summarize_sources")
builder.add_edge("summarize_sources", "reflect_on_summary")
builder.add_conditional_edges("reflect_on_summary", route_research)
builder.add_edge("finalize_summary", END)

graph = builder.compile()
