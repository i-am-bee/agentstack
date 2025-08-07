# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.client import create_text_message_object
from a2a.types import Message, TaskState, TaskStatus

from beeai_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from beeai_sdk.a2a.extensions.ui.trajectory import TrajectoryExtensionServer, TrajectoryExtensionSpec
from beeai_sdk.a2a.types import RunYield
from beeai_sdk.server import Server
from beeai_sdk.server.context import Context

server = Server()


@server.agent()
async def dependent_agent(
    message: Message,
    context: Context,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    # does not typecheck, does not ruff check
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
) -> AsyncGenerator[RunYield, Message]:
    """Awaits a user message"""

    yield trajectory.trajectory_metadata(title="context_param", content=str(context))
    yield trajectory.trajectory_metadata(title="message_param", content=str(message.model_dump()))
    yield trajectory.message(trajectory_title="llm_param", trajectory_content=str(llm.data))

    message = yield TaskStatus(
        message=create_text_message_object(content="give me auth\n"), state=TaskState.auth_required
    )
    yield trajectory.message(trajectory_title="follow up message", trajectory_content=str(message))


if __name__ == "__main__":
    server.run(self_registration=False)
