# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.auth.secrets import (
    SecretDemand,
    SecretsExtensionServer,
    SecretsExtensionSpec,
    SecretsServiceExtensionParams,
)
from agentstack_sdk.server import Server

server = Server()


@server.agent()
async def basic_secrets_example(
    input: Message,
    secrets: Annotated[
        SecretsExtensionServer,
        SecretsExtensionSpec.single_demand(key="SLACK_API_KEY", name="Slack", description="Access to Slack"),
    ],
):
    """Agent that requests a secret that can be provided during runtime"""
    if secrets and secrets.data and secrets.data.secret_fulfillments:
        yield f"Slack API key: {secrets.data.secret_fulfillments['SLACK_API_KEY'].secret.get_secret_value()}"
    else:
        try:
            runtime_provided_secrets = await secrets.request_secrets(
                params=SecretsServiceExtensionParams(
                    secret_demands={"SLACK_API_KEY": SecretDemand(description="I really need Slack Key", name="Slack")}
                )
            )
        except ValueError:
            runtime_provided_secrets = None

        if runtime_provided_secrets and runtime_provided_secrets.secret_fulfillments:
            yield f"Slack API key: {runtime_provided_secrets.secret_fulfillments['SLACK_API_KEY'].secret.get_secret_value()}"
        else:
            yield "No Slack API key provided"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
