# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import List, Callable
from crewai import Agent, Crew, Process, Task, LLM
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field


class MarketStrategy(BaseModel):
    """Market strategy model"""

    name: str = Field(..., description="Name of the market strategy")
    tatics: List[str] = Field(..., description="List of tactics to be used in the market strategy")
    channels: List[str] = Field(..., description="List of channels to be used in the market strategy")
    KPIs: List[str] = Field(..., description="List of KPIs to be used in the market strategy")


class CampaignIdea(BaseModel):
    """Campaign idea model"""

    name: str = Field(..., description="Name of the campaign idea")
    description: str = Field(..., description="Description of the campaign idea")
    audience: str = Field(..., description="Audience of the campaign idea")
    channel: str = Field(..., description="Channel of the campaign idea")


class Copy(BaseModel):
    """Copy model"""

    title: str = Field(..., description="Title of the copy")
    body: str = Field(..., description="Body of the copy")


def create_marketing_crew(llm: LLM, step_callback: Callable):
    lead_market_analyst = Agent(
        role="Lead Market Analyst",
        tools=[SerperDevTool(), ScrapeWebsiteTool()],
        goal=(
            "Conduct amazing analysis of the products and competitors, providing in-depth "
            "insights to guide marketing strategies."
        ),
        backstory=(
            "As the Lead Market Analyst at a premier digital marketing firm, you specialize "
            "in dissecting online business landscapes."
        ),
        verbose=True,
        llm=llm,
    )

    chief_marketing_strategist = Agent(
        role="Chief Marketing Strategist",
        goal="Synthesize amazing insights from product analysis to formulate incredible marketing strategies.",
        backstory=(
            "You are the Chief Marketing Strategist at a leading digital marketing agency, "
            "known for crafting bespoke strategies that drive success."
        ),
        tools=[SerperDevTool(), ScrapeWebsiteTool()],
        verbose=True,
        llm=llm,
    )

    creative_content_creator = Agent(
        role="Creative Content Creator",
        goal=(
            "Develop compelling and innovative content for social media campaigns, with a "
            "focus on creating high-impact ad copies."
        ),
        backstory=(
            "As a Creative Content Creator at a top-tier digital marketing agency, you "
            "excel in crafting narratives that resonate with audiences. Your expertise "
            "lies in turning marketing strategies into engaging stories and visual "
            "content that capture attention and inspire action."
        ),
        verbose=True,
        llm=llm,
    )

    research_task = Task(
        description=(
            "Conduct a thorough research about the customer and competitors. "
            "Make sure you find any interesting and relevant information given the "
            "current year is 2024. "
            "We are working with them on the following project: {project_description}."
        ),
        expected_output=(
            "A complete report on the customer and their customers and competitors, "
            "including their demographics, preferences, market positioning and audience engagement."
        ),
        agent=lead_market_analyst,
    )

    project_understanding_task = Task(
        description=(
            "Understand the project details and the target audience for "
            "{project_description}. "
            "Review any provided materials and gather additional information as needed."
        ),
        expected_output="A detailed summary of the project and a profile of the target audience.",
        agent=chief_marketing_strategist,
    )

    marketing_strategy_task = Task(
        description=(
            "Formulate a comprehensive marketing strategy for the project "
            "{project_description} of the customer. "
            "Use the insights from the research task and the project understanding "
            "task to create a high-quality strategy."
        ),
        expected_output=(
            "A detailed marketing strategy document that outlines the goals, target "
            "audience, key messages, and proposed tactics, make sure to have name, tactics, "
            "channels and KPIs"
        ),
        agent=chief_marketing_strategist,
        output_json=MarketStrategy,
    )

    campaign_idea_task = Task(
        description=(
            "Develop creative marketing campaign ideas for {project_description}. "
            "Ensure the ideas are innovative, engaging, and aligned with the overall marketing strategy."
        ),
        expected_output="A list of 5 campaign ideas, each with a brief description and expected impact.",
        agent=creative_content_creator,
        output_json=CampaignIdea,
    )

    copy_creation_task = Task(
        description=(
            "Create marketing copies based on the approved campaign ideas for {project_description}. "
            "Ensure the copies are compelling, clear, and tailored to the target audience."
        ),
        expected_output="Marketing copies for each campaign idea.",
        agent=creative_content_creator,
        context=[marketing_strategy_task, campaign_idea_task],
        output_json=Copy,
    )

    return Crew(
        agents=[lead_market_analyst, chief_marketing_strategist, creative_content_creator],
        tasks=[
            research_task,
            project_understanding_task,
            marketing_strategy_task,
            campaign_idea_task,
            copy_creation_task,
        ],
        process=Process.sequential,
        verbose=True,
        step_callback=step_callback,
    )
