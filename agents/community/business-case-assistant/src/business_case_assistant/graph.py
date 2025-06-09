from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END, MessagesState
from langchain_openai import ChatOpenAI
from business_case_assistant.configuration import Configuration
import os

from business_case_assistant.nodes import(BusinessCaseState, 
    gather_requirements, 
    write_alternatives_and_analysis, 
    write_introduction, 
    write_executive_summary, 
    write_general_project_information, 
    write_high_level_business_impact, 
    write_preferred_solution, 
    compile_document, 
    route_gather)

config = Configuration()

small_model = ChatOpenAI(
        model=config.llm_model,
        openai_api_key=config.llm_api_key,
        openai_api_base=config.llm_api_base,
        temperature=0,
        max_tokens=2000
    )

medium_model = ChatOpenAI(
        model=config.llm_model,
        openai_api_key=config.llm_api_key,
        openai_api_base=config.llm_api_base,
        temperature=0,
        max_tokens=4000
    )
    

def build_graph():
    # Create the graph
    graph = StateGraph(BusinessCaseState, input= MessagesState)

    # Add nodes to the graph
    graph.add_node("Gathering Requirements", lambda state: gather_requirements(state, small_model))
    graph.add_node("Writing Introduction",lambda state: write_introduction(state, small_model))
    graph.add_node("Writing General Project Information", lambda state: write_general_project_information(state, medium_model))
    graph.add_node("Writing High Level Business Impact", lambda state: write_high_level_business_impact(state, medium_model))
    graph.add_node("Writing Alternatives and Analysis", lambda state: write_alternatives_and_analysis(state, small_model, medium_model))
    graph.add_node("Writing Preferred Solution", lambda state: write_preferred_solution(state, medium_model))
    graph.add_node("Writing Executive Summary",lambda state: write_executive_summary(state, small_model))
    graph.add_node("Compiling Document", compile_document)

    # Define the edges
    graph.set_entry_point("Gathering Requirements")
    graph.add_conditional_edges("Gathering Requirements", route_gather)
    graph.add_edge("Writing Introduction", "Writing General Project Information")
    graph.add_edge("Writing Introduction", "Writing High Level Business Impact")
    graph.add_edge("Writing Introduction", "Writing Alternatives and Analysis")
    graph.add_edge("Writing Introduction", "Writing Preferred Solution")
    graph.add_edge(
        ["Writing General Project Information", 
        "Writing High Level Business Impact", 
        "Writing Alternatives and Analysis", 
        "Writing Preferred Solution"], 
        "Writing Executive Summary")
    graph.add_edge("Writing Executive Summary", "Compiling Document")
    graph.add_edge("Compiling Document", END)

    return graph

graph = build_graph().compile()