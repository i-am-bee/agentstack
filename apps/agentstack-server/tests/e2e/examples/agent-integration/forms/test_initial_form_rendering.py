# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up")
async def initial_form_rendering_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/forms/initial-form-rendering"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("test case description"):
            pass