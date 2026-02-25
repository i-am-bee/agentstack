# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from agentstack_server.domain.constants import AGENT_DETAIL_EXTENSION_URI
from agentstack_server.utils.a2a import get_extension
from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_basic_configuration_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/agent-details/basic-configuration"

    async with run_example(example_path, a2a_client_factory) as running_example:
        agent_card = running_example.agent_card

        with subtests.test("agent card has correct name"):
            assert agent_card.name == "Example Research Assistant"

        with subtests.test("agent card has two skills"):
            assert agent_card.skills is not None
            assert len(agent_card.skills) == 2

            skill_ids = {skill.id for skill in agent_card.skills}
            assert skill_ids == {"research", "summarization"}

        with subtests.test("agent detail extension is configured"):
            agent_detail = get_extension(agent_card, AGENT_DETAIL_EXTENSION_URI)
            assert agent_detail is not None

            params = agent_detail.model_dump()["params"]
            assert params["interaction_mode"] == "multi-turn"
            assert (
                params["user_greeting"] == "Hi there! I can help you research topics or summarize uploaded documents."
            )
            assert params["framework"] == "BeeAI Framework"
            assert params["source_code_url"] == "https://github.com/example/example-research-assistant"

        with subtests.test("agent detail has author info"):
            agent_detail = get_extension(agent_card, AGENT_DETAIL_EXTENSION_URI)
            params = agent_detail.model_dump()["params"]

            assert params["author"]["name"] == "Agent Stack Team"
            assert params["author"]["email"] == "team@example.com"

        with subtests.test("agent detail has tools"):
            agent_detail = get_extension(agent_card, AGENT_DETAIL_EXTENSION_URI)
            params = agent_detail.model_dump()["params"]

            tools = params["tools"]
            assert len(tools) == 2

            tool_names = {tool["name"] for tool in tools}
            assert tool_names == {"Web Search", "Document Reader"}
