# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from langgraph.graph import END, MessagesState
from typing import Literal
from langchain_core.messages import RemoveMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool


# Define the state for the graph, extending MessagesState
class BusinessCaseState(MessagesState):
    introduction: str
    general_project_information: str
    high_level_business_impact: str
    alternatives_and_analysis: str
    preferred_solution: str
    executive_summary: str
    document: str
    requirements: str
    next: str
    next_instructions: str
    message_summary: str


introduction_intructions = """A Business Case assists organizational stakeholders in making decisions regarding the viability of a proposed\
    project effort. Use of a Business Case is considered standard practice throughout private and public industry.\
    In government there are also specific laws and regulations that mandate the use of Business Cases for certain project types.\
    For additional information regarding Business Case requirements contact the appropriate Capital Planning and Investment Control Office(r)."""

gpi_intructions = """PROJECT DESCRIPTION\
    Business Need\
    Enter a detailed explanation of the business need/issue/problem that the requested project will\
    address. Include any expected benefits from the investment of organizational resources into the project\
    Goals/Scope\
    Enter a detailed description of the purpose, goals, and scope of the proposed project.\
    Detail expected short-term, long-term, and operational goals and objectives.\
    Enter a detailed explanation of how the proposed project aligns with, or advances, organizational\
    goals and objectives, and avoids duplication of any enterprise architecture components.\
    Risks/Issues\
    Enter basic business and technical risks/issues of executing and/or not executing the project. 
    OMB risk areas include: Schedule, Initial Costs, Life-cycle Costs, Technical Obsolescence,\
    Feasibility, Reliability of Systems, Dependencies/Interoperability, Surety Considerations,\
    Future Procurements, Project Management, Overall Project Failure, Organizational/Change Management,\
    Business, Data/Information, Technology, Strategic, Security, Privacy, Project Resources.
    """

biz_instructions = """Outline, at a high-level, what business functions/processes may be impacted, and\
    how, by the project for it to be successfully implemented. Describe plans for  \
    addressing ongoing operations, future growth, and how this will be addressed and\
    managed. Consider not only the requirements for additional hardware, software,\
    building materials, and space but also where financial funding for these things will\
    come from, additional resource requirements, staffing, training, other expenditures,\
    etc. Also describe how investment performance will be measured. Identify specific\
    performance indicators that may be used to measure investment outcomes and its\
    progress in addressing the particular business need."""

solution_instructions = """PREFERRED SOLUTION
    Financial Considerations\
    Identify funding sources for all project component costs for the preferred solution.\
    This should include consideration of items such as capital costs, operating costs,\
    total cost of ownership, impact on other projects, funding requirements, etc.\
    Prelminary Acquisition Strategy/Plan\
    Identify acquisition sources for the preferred solution that includes all project\
    supplies, services, and commercial items. Its important to note that the PM is not\
    necessarily directly involved in the procurement of supplies or services. Often the\
    individual designated as the Procurement Officer acts as a liaison between the\
    project team and the Procurement and Grants Office (PGO) to communicate\
    project acquisition requirements.\
    Preliminary Work Breakdown Structure\
    Include a Work Breakdown Structure (WBS) for the preferred solution. The WBS\
    organizes and defines 100% of the scope of project work to be accomplished and\
    displays it in a way that relates work elements to each other and to the projects goals.\
    Assumptions And Constraints\
    Include a detailed explanation of any assumptions and/or constraints applied to\
    the information documented within this business case.\
    """
alt_analysis_instructions = """The Alternative Analysis section should identify options and alternatives to the proposed project 
and the strategy used to identify and define them. Include a description of the approaches for the identification of alternatives 
and an outline/description of each alternative considered. Include at least three viable alternatives: keeping things “as-is” or 
reuse existing people, equipment, or processes; and at least two additional alternatives. 
Some examples of alternatives to consider may include:
•	Buy vs. build vs. lease vs. reuse of existing system
•	Outsource vs. in-house development
•	Commercial off the shelf (COTS) vs. Government off the shelf (GOTS)
•	Mainframe vs. server-based vs. clustering
•	Unix vs. Linux vs. Windows]
Include a detailed alternative analysis that contains information such as:
•	Cost/benefit analysis
•	Initial and ongoing costs
•	Payback period
•	Return on investment (ROI)
•	Other financial consideration
•	Security considerations
•	Etc"""


# Define the logic for each node
def gather_requirements(state: BusinessCaseState, model) -> BusinessCaseState:
    gather_prompt = """You are tasked with helping write a business use case document.\
    Your first job is to gather all the user requirements about the project.\
    You should have a clear sense of all the needs of each stage the project.\
    You are conversing with a user. Ask as many follow up questions as necessary - but only ask ONE question at a time.\
    You only need to gather enough information to write a draft. The can follow-up after you write the draft. \
     If you have a good idea of what they are trying to build and have enough information to write the section, \
    call the `WriteRequirements` tool with a detailed description.\
    """

    @tool
    def WriteRequirements(requirements):
        """
        If you have a good idea of what they are trying to build and have enough information to write the section, \
        call the this tool.\
        Args: requirements
        """
        return requirements

    messages = [
        {"role": "system", "content": gather_prompt},
    ] + state["messages"]

    model_write = model.bind_tools([WriteRequirements])
    response = model_write.invoke(messages)
    print(response.tool_calls)
    if len(response.tool_calls) == 0:
        return {"messages": [response]}
    else:
        requirements = WriteRequirements.invoke(response.tool_calls[0]).content
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:1]]
        return {"requirements": requirements, "messages": delete_messages}


def write_introduction(state: BusinessCaseState, model) -> BusinessCaseState:
    introduction_prompt = """ You are tasked with writing the Introduction section to a business case document\
    take the requirements that have obtained from the user and summerize them into a introduction using the following\
    intructions as a guide.
    Intructions: {instructions}
    """

    messages = [
        {"role": "system", "content": introduction_prompt.format(instructions=introduction_intructions)},
        {"role": "user", "content": state["requirements"]},
    ]

    introduction_chain = model | StrOutputParser()
    introduction = introduction_chain.invoke(messages)

    return {
        "introduction": introduction,
    }


def write_general_project_information(state: BusinessCaseState, model) -> BusinessCaseState:
    gpi_prompt = """You are tasked with writing the General Project Information of a Business Case.\
          Take the requirements you obtained from the user and write the section using the following instructions:
           {instructions} 
           """

    messages = [
        {"role": "system", "content": gpi_prompt.format(instructions=gpi_intructions)},
        {"role": "user", "content": state["requirements"]},
    ]

    gpi_chain = model | StrOutputParser()
    gpi = gpi_chain.invoke(messages)
    return {
        "general_project_information": gpi,
    }


def write_high_level_business_impact(state: BusinessCaseState, model) -> BusinessCaseState:
    impact_prompt = """You are tasked with writing the High Level Business Impact of a business case document.\
    Take the requirements obtained from the user and write the section using the following instructions as a guide.\
            Instructions: {instructions} """

    messages = [
        {"role": "system", "content": impact_prompt.format(instructions=biz_instructions)},
        {"role": "user", "content": state["requirements"]},
    ]
    biz_chain = model | StrOutputParser()
    biz_impact = biz_chain.invoke(messages)
    return {"high_level_business_impact": biz_impact}


def write_alternatives_and_analysis(state: BusinessCaseState, small_model, medium_model) -> BusinessCaseState:
    alt_analysis_prompt = """You are an expert Business Case Writer take the users requirements and ideas\
        using the following instructions {instructions}
        User Requirements: {requirements}"""

    messages = messages = [
        {
            "role": "system",
            "content": alt_analysis_prompt.format(
                instructions=alt_analysis_instructions, requirements=state["requirements"]
            ),
        },
        {"role": "user", "content": state["requirements"]},
    ]
    alt_analysis_chain = medium_model | StrOutputParser()
    alt_analysis = alt_analysis_chain.invoke(messages)

    return {
        "alternatives_and_analysis": alt_analysis,
    }


def write_preferred_solution(state: BusinessCaseState, model) -> BusinessCaseState:
    solution_prompt = """You are tasked with writing the Preferred Solutions section to a business case document.\
        Take the requirements that you have obtained from the user and write the section using the following instructions as a guide.\
        Instructions: {instructions}
        """

    messages = [
        {"role": "system", "content": solution_prompt.format(instructions=solution_instructions)},
        {"role": "user", "content": state["requirements"]},
    ]
    solution_chain = model | StrOutputParser()
    solution = solution_chain.invoke(messages)
    return {
        "preferred_solution": solution,
    }


def write_executive_summary(state: BusinessCaseState, model) -> BusinessCaseState:
    first_draft_doc = (
        str(state["introduction"])
        + str(state["general_project_information"])
        + str(state["high_level_business_impact"])
        + str(state["alternatives_and_analysis"])
        + str(state["preferred_solution"])
    )
    exe_sum_prompt = """You are tasked with the writing the executive summary of a Buisness Case.\
        Take the draft you obtained from the user and create write a short executive summmary\
        no more 3-5 sentences: """

    messages = [{"role": "system", "content": exe_sum_prompt}, {"role": "user", "content": first_draft_doc}]
    exe_sum_chain = model | StrOutputParser()
    exe_sum = exe_sum_chain.invoke(messages)

    draft_doc = (
        str(exe_sum)
        + "\n\n"
        + str(state["introduction"])
        + "\n\n"
        + str(state["general_project_information"])
        + "\n\n"
        + str(state["high_level_business_impact"])
        + "\n\n"
        + str(state["alternatives_and_analysis"])
        + "\n\n"
        + str(state["preferred_solution"])
    )
    return {"executive_summary": exe_sum, "document": draft_doc}


def compile_document(state: BusinessCaseState) -> BusinessCaseState:
    final_doc = (
        str(state["executive_summary"])
        + "\n\n"
        + str(state["introduction"])
        + "\n\n"
        + str(state["general_project_information"])
        + "\n\n"
        + str(state["high_level_business_impact"])
        + "\n\n"
        + str(state["alternatives_and_analysis"])
        + "\n\n"
        + str(state["preferred_solution"])
    )

    return {"document": final_doc}


def route_gather(state: BusinessCaseState) -> Literal["Writing Introduction", END]:
    if state.get("requirements"):
        return "Writing Introduction"
    else:
        return END
