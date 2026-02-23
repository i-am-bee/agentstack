# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.types import AgentSkill

from agentstack_sdk.a2a.extensions.ui.agent_detail import AgentDetailExtensionSpec
from agentstack_sdk.server.agent import agent


@pytest.mark.unit
def test_agent_detail_population():
    skill = AgentSkill(
        id="skill-1",
        name="test_skill",
        description="A test skill",
        input_modes=[],
        output_modes=[],
        tags=[],
    )
    description = "Test Description"

    @agent(skills=[skill], description=description)
    def test_agent_fn():
        pass

    def mock_modify_dependencies(deps):
        pass

    # test_agent_fn is now the agent_factory
    agent_instance = test_agent_fn(mock_modify_dependencies)

    extensions = agent_instance.card.capabilities.extensions
    assert extensions is not None

    detail_extension = next((ext for ext in extensions if ext.uri == AgentDetailExtensionSpec.URI), None)
    assert detail_extension is not None

    params = detail_extension.params
    assert params is not None

    # Check tools populated from skills
    assert "tools" in params
    tools = params["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "test_skill"
    assert tools[0]["description"] == "A test skill"

    # Check user_greeting populated from description
    assert "user_greeting" in params
    assert params["user_greeting"] == description

    # Check default input_placeholder
    assert "input_placeholder" in params
    assert params["input_placeholder"] == "What is your task?"


@pytest.mark.unit
def test_agent_detail_population_override():
    skill = AgentSkill(
        id="skill-1",
        name="test_skill",
        description="A test skill",
        input_modes=[],
        output_modes=[],
        tags=[],
    )
    description = "Test Description"

    from agentstack_sdk.a2a.extensions.ui.agent_detail import AgentDetail

    custom_detail = AgentDetail(user_greeting="Custom Greeting", input_placeholder="Custom Placeholder")

    @agent(skills=[skill], description=description, detail=custom_detail)
    def test_agent_fn():
        pass

    def mock_modify_dependencies(deps):
        pass

    agent_instance = test_agent_fn(mock_modify_dependencies)

    extensions = agent_instance.card.capabilities.extensions
    assert extensions
    detail_extension = next((ext for ext in extensions if ext.uri == AgentDetailExtensionSpec.URI), None)
    assert detail_extension
    params = detail_extension.params
    assert params

    # Tools should still be populated because custom_detail.tools was None
    assert "tools" in params
    tools = params["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "test_skill"

    # Greeting should be custom
    assert params["user_greeting"] == "Custom Greeting"

    # Placeholder should be custom
    assert params["input_placeholder"] == "Custom Placeholder"


@pytest.mark.unit
def test_agent_detail_explicit_empty_values():
    skill = AgentSkill(
        id="skill-1",
        name="test_skill",
        description="A test skill",
        input_modes=[],
        output_modes=[],
        tags=[],
    )
    description = "Test Description"

    from agentstack_sdk.a2a.extensions.ui.agent_detail import AgentDetail

    # Explicitly empty tools and greeting
    custom_detail = AgentDetail(tools=[], user_greeting="", input_placeholder="")

    @agent(skills=[skill], description=description, detail=custom_detail)
    def test_agent_fn():
        pass

    def mock_modify_dependencies(deps):
        pass

    agent_instance = test_agent_fn(mock_modify_dependencies)

    extensions = agent_instance.card.capabilities.extensions
    detail_extension = next((ext for ext in extensions if ext.uri == AgentDetailExtensionSpec.URI), None)
    assert detail_extension
    params = detail_extension.params
    assert params

    # Tools should remain empty list, not populated from skills
    assert "tools" in params
    assert params["tools"] == []

    # Greeting should remain empty string, not populated from description
    assert "user_greeting" in params
    assert params["user_greeting"] == ""

    # Placeholder should remain empty string, not populated from default
    assert "input_placeholder" in params
    assert params["input_placeholder"] == ""
