# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import logging

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    TaskState,
)
from beeai_sdk.platform import BuildState, Provider, ProviderBuild

pytestmark = pytest.mark.e2e

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_remote_agent_build_and_start(
    subtests,
    a2a_client_factory,
    get_final_task_from_stream,
    test_configuration,
):
    with subtests.test("build example agent"):
        build = await ProviderBuild.create(location=test_configuration.test_agent_build_repo)
        async for message in build.stream_logs():
            logger.debug(json.dumps(message))
        build = await build.get()

        assert build.status == BuildState.COMPLETED
    with subtests.test("run example agent"):
        _ = await Provider.create(location=build.destination)
        providers = await Provider.list()
        assert len(providers) == 1
        assert providers[0].source == build.destination
        assert providers[0].agent_card

        async with a2a_client_factory(providers[0].agent_card) as a2a_client:
            message = create_text_message_object(content="test of sirens")
            task = await get_final_task_from_stream(a2a_client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "test of sirens" in task.history[-1].parts[0].root.text
