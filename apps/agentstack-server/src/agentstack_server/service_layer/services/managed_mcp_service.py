# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging

from fastapi import status
from kink import inject
from pydantic import AnyUrl

from agentstack_server.configuration import Configuration, ConnectorPreset
from agentstack_server.domain.models.connector import Connector
from agentstack_server.exceptions import PlatformError
from agentstack_server.utils.kubectl import Kubectl

logger = logging.getLogger(__name__)


@inject
class ManagedMcpService:
    def __init__(self, configuration: Configuration, kubectl: Kubectl):
        self._configuration = configuration
        self._kubectl = kubectl

    def find_preset(self, url: AnyUrl) -> ConnectorPreset | None:
        return next((p for p in self._configuration.connector.presets if str(p.url) == str(url)), None)

    def is_managed(self, *, connector: Connector) -> bool:
        return (preset := self.find_preset(connector.url)) is not None and preset.url.scheme == "mcp+stdio"

    def get_service_url(self, *, connector: Connector) -> str:
        return f"http://managed-mcp-supergateway-{connector.id.hex[:16]}.{self._kubectl._default_kwargs['namespace']}.svc.cluster.local:8080"

    async def deploy(self, *, connector: Connector, preset: ConnectorPreset) -> None:
        assert preset.stdio
        try:
            await self._kubectl.apply(
                "-f",
                "-",
                input={
                    "apiVersion": "v1",
                    "kind": "List",
                    "items": [
                        {
                            "apiVersion": "apps/v1",
                            "kind": "Deployment",
                            "metadata": {
                                "name": f"managed-mcp-server-{connector.id.hex[:16]}",
                                "labels": {
                                    "app": "managed-mcp-server",
                                    "connector-id": str(connector.id),
                                },
                            },
                            "spec": {
                                "replicas": 1,
                                "selector": {
                                    "matchLabels": {
                                        "app": "managed-mcp-server",
                                        "connector-id": str(connector.id),
                                    }
                                },
                                "template": {
                                    "metadata": {
                                        "labels": {
                                            "app": "managed-mcp-server",
                                            "connector-id": str(connector.id),
                                        }
                                    },
                                    "spec": {
                                        "automountServiceAccountToken": False,
                                        "containers": [
                                            {
                                                "name": "mcp-server",
                                                "image": preset.stdio.image,
                                                "imagePullPolicy": "IfNotPresent",
                                                "stdin": True,
                                                "tty": False,
                                                **(
                                                    {}
                                                    if not preset.stdio.command
                                                    else {"command": preset.stdio.command}
                                                ),
                                                **({} if not preset.stdio.args else {"args": preset.stdio.args}),
                                                **(
                                                    {}
                                                    if not preset.stdio.env
                                                    and not (
                                                        connector.auth
                                                        and connector.auth.token
                                                        and preset.stdio.auth_token_env_name
                                                    )
                                                    else {
                                                        "env": [
                                                            {"name": k, "value": v}
                                                            for k, v in (preset.stdio.env or {}).items()
                                                        ]
                                                        + (
                                                            [
                                                                {
                                                                    "name": preset.stdio.auth_token_env_name,
                                                                    "value": connector.auth.token.access_token,
                                                                }
                                                            ]
                                                            if connector.auth
                                                            and connector.auth.token
                                                            and preset.stdio.auth_token_env_name
                                                            else []
                                                        )
                                                    }
                                                ),
                                            },
                                        ],
                                    },
                                },
                            },
                        },
                        {
                            "apiVersion": "apps/v1",
                            "kind": "Deployment",
                            "metadata": {
                                "name": f"managed-mcp-supergateway-{connector.id.hex[:16]}",
                                "labels": {
                                    "app": "managed-mcp-supergateway",
                                    "connector-id": str(connector.id),
                                },
                            },
                            "spec": {
                                "replicas": 1,
                                "selector": {
                                    "matchLabels": {
                                        "app": "managed-mcp-supergateway",
                                        "connector-id": str(connector.id),
                                    }
                                },
                                "template": {
                                    "metadata": {
                                        "labels": {
                                            "app": "managed-mcp-supergateway",
                                            "connector-id": str(connector.id),
                                        }
                                    },
                                    "spec": {
                                        "serviceAccountName": "managed-mcp-supergateway",
                                        "containers": [
                                            {
                                                "name": "supergateway",
                                                "image": "ghcr.io/i-am-bee/agentstack/supergateway:latest",
                                                "imagePullPolicy": "IfNotPresent",
                                                "command": ["supergateway"],
                                                "args": [
                                                    "--stdio",
                                                    f"kubectl attach $(kubectl get pod -l app=managed-mcp-server,connector-id={connector.id} -o jsonpath='{{.items[0].metadata.name}}') -c mcp-server --stdin --tty=false",
                                                    "--outputTransport",
                                                    "streamableHttp",
                                                    "--stateful",
                                                    "--port",
                                                    "8080",
                                                    "--streamableHttpPath",
                                                    "/mcp",
                                                    "--logLevel",
                                                    "info",
                                                ],
                                                "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                                                "readinessProbe": {
                                                    "tcpSocket": {"port": 8080},
                                                    "initialDelaySeconds": 2,
                                                    "periodSeconds": 5,
                                                    "failureThreshold": 3,
                                                },
                                            },
                                        ],
                                    },
                                },
                            },
                        },
                        {
                            "apiVersion": "v1",
                            "kind": "Service",
                            "metadata": {"name": f"managed-mcp-supergateway-{connector.id.hex[:16]}"},
                            "spec": {
                                "selector": {
                                    "app": "managed-mcp-supergateway",
                                    "connector-id": str(connector.id),
                                },
                                "ports": [
                                    {
                                        "name": "http",
                                        "port": 8080,
                                        "targetPort": 8080,
                                        "protocol": "TCP",
                                    }
                                ],
                            },
                        },
                    ],
                },
            )
        except RuntimeError as err:
            raise PlatformError(
                f"Failed to create MCP server deployment: {err}",
                status_code=status.HTTP_502_BAD_GATEWAY,
            ) from err

        try:
            await self._kubectl.wait(
                f"deployment/managed-mcp-server-{connector.id.hex[:16]}",
                _for="condition=Available",
                timeout="60s",
            )
            await self._kubectl.wait(
                f"deployment/managed-mcp-supergateway-{connector.id.hex[:16]}",
                _for="condition=Available",
                timeout="60s",
            )
        except RuntimeError as err:
            raise PlatformError(
                "Managed MCP deployment failed to become ready",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            ) from err

    async def undeploy(self, *, connector: Connector) -> None:
        for resource_type, resource_name in (
            ("deployment", f"managed-mcp-server-{connector.id.hex[:16]}"),
            ("deployment", f"managed-mcp-supergateway-{connector.id.hex[:16]}"),
            ("service", f"managed-mcp-supergateway-{connector.id.hex[:16]}"),
        ):
            try:
                await self._kubectl.delete(resource_type, resource_name, ignore_not_found=True)
            except RuntimeError as err:
                logger.warning("Failed to delete %s/%s: %s", resource_type, resource_name, err)
