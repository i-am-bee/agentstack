# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
import logging

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    TaskState,
)
from agentstack_sdk.platform import AddProvider, BuildState, Provider, ProviderBuild
from agentstack_sdk.platform.context import Context

pytestmark = pytest.mark.e2e

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_remote_agent_build_and_start(
    subtests,
    a2a_client_factory,
    get_final_task_from_stream,
    test_configuration,
):
    with subtests.test("preview build"):
        build = await ProviderBuild.preview(location=test_configuration.test_agent_build_repo)
        assert build.destination
    with subtests.test("build example agent"):
        build = await ProviderBuild.create(location=test_configuration.test_agent_build_repo, on_complete=AddProvider())
        async for message in build.stream_logs():
            logger.debug(json.dumps(message))

        for _ in range(10):
            build = await build.get()
            if build.status != BuildState.IN_PROGRESS:
                break
            await asyncio.sleep(0.5)

        assert build.status == BuildState.COMPLETED, f"Fail: {build.error_message}"
    with subtests.test("run example agent"):
        providers = await Provider.list()
        assert len(providers) == 1
        provider = providers[0]
        assert provider.source == build.destination
        assert provider.id == build.provider_id
        assert provider.agent_card
        assert test_configuration.test_agent_build_repo in provider.origin

        context = await Context.create()
        context_token = await context.generate_token(providers={provider.id})

        async with a2a_client_factory(provider.agent_card, context_token) as a2a_client:
            message = create_text_message_object(content="test of sirens")
            task = await get_final_task_from_stream(a2a_client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "test of sirens" in task.history[-1].parts[0].root.text
