# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message

from beeai_sdk.a2a.extensions.auth.secrets import (
    SecretDemand,
    SecretsExtensionServer,
    SecretsExtensionSpec,
    SecretsServiceExtensionParams,
)
from beeai_sdk.server import Server

server = Server()


@server.agent()
async def secrets_agent(
    input: Message,
    secrets: Annotated[
        SecretsExtensionServer,
        SecretsExtensionSpec.single_demand(name="Slack", description="Slack API key"),
    ],
):
    """Agent that uses request a secret that can be provided during runtime"""
    if secrets and secrets.data and secrets.data.secret_fulfillments:
        yield f"Slack API key: {secrets.data.secret_fulfillments['default'].secret}"
    else:
        runtime_provided_secrets = await secrets.request_secrets(
            params=SecretsServiceExtensionParams(
                secret_demands={"default": SecretDemand(description="I really need Slack Key", name="Slack")}
            )
        )
        if runtime_provided_secrets and runtime_provided_secrets.secret_fulfillments:
            yield f"Slack API key: {runtime_provided_secrets.secret_fulfillments['default'].secret}"
        else:
            yield "No Slack API key provided"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
