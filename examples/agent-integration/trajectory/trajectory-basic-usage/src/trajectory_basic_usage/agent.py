# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from time import sleep
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions import TrajectoryExtensionServer, TrajectoryExtensionSpec
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent(
    name="Docs Trajectory Agent",
)
async def trajectory_basic_usage_example(
    input: Message, context: RunContext, trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()]
):
    yield trajectory.trajectory_metadata(
        title="Planning", content="Analyzing the user request to determine the best approach..."
    )
    sleep(3)  # Sleep so that you can watch the trajectory steps unfold

    yield trajectory.trajectory_metadata(title="Execution", content="Processing data with temperature=0.7...")
    sleep(3)

    yield "Final result goes here"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
