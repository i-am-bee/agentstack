# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_%{EXAMPLE_NAME_SNAKE_CASE}_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "%{EXAMPLE_PATH}"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("test case description"):
            pass