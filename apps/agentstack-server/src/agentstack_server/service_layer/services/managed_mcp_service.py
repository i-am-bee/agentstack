# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import kr8s
from fastapi import status
from kr8s.asyncio.objects import Deployment, Secret, Service
from pydantic import AnyUrl

from agentstack_server.configuration import Configuration, ConnectorPreset
from agentstack_server.domain.models.connector import Connector
from agentstack_server.exceptions import PlatformError

logger = logging.getLogger(__name__)


class ManagedMcpService:
    def __init__(
        self,
        configuration: Configuration,
        api_factory: Callable[[], Awaitable[kr8s.asyncio.Api]],
    ):
        self._configuration = configuration
        self._api_factory = api_factory
        self._namespace = ""  # filled in on first deploy

    @asynccontextmanager
    async def api(self) -> AsyncIterator[kr8s.asyncio.Api]:
        yield await self._api_factory()

    def find_preset(self, url: AnyUrl) -> ConnectorPreset | None:
        return next((p for p in self._configuration.connector.presets if str(p.url) == str(url)), None)

    def is_managed(self, *, connector: Connector) -> bool:
        return (preset := self.find_preset(connector.url)) is not None and preset.url.scheme == "mcp+stdio"

    def get_service_url(self, *, connector: Connector) -> str:
        return f"http://managed-mcp-supergateway-{connector.id.hex[:16]}.{self._namespace}.svc.cluster.local:8080"

    async def deploy(self, *, connector: Connector, preset: ConnectorPreset) -> None:
        assert preset.stdio
        async with self.api() as api:
            self._namespace = api.namespace

            secret = Secret(
                {
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {
                        "name": f"managed-mcp-server-env-{connector.id.hex[:16]}",
                        "labels": {
                            "app": "managed-mcp-server",
                            "connector-id": str(connector.id),
                        },
                    },
                    "type": "Opaque",
                    "stringData": (preset.stdio.env or {})
                    | (
                        {preset.stdio.access_token_env_name: connector.auth.token.access_token}
                        if connector.auth and connector.auth.token and preset.stdio.access_token_env_name
                        else {}
                    ),
                },
                api=api,
            )

            mcp_server_deployment = Deployment(
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
                                        "envFrom": [
                                            {"secretRef": {"name": f"managed-mcp-server-env-{connector.id.hex[:16]}"}}
                                        ],
                                        **({} if not preset.stdio.command else {"command": preset.stdio.command}),
                                        **({} if not preset.stdio.args else {"args": preset.stdio.args}),
                                    },
                                ],
                            },
                        },
                    },
                },
                api=api,
            )

            supergateway_deployment = Deployment(
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
                api=api,
            )

            service = Service(
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
                api=api,
            )

            try:
                await secret.create()
                await mcp_server_deployment.create()
                await supergateway_deployment.create()
                await service.create()
                await mcp_server_deployment.wait("condition=Available", timeout=60)
                await supergateway_deployment.wait("condition=Available", timeout=60)
            except Exception as err:
                await self.undeploy(connector=connector)
                raise PlatformError(
                    f"Failed to create MCP server deployment: {err}",
                    status_code=status.HTTP_502_BAD_GATEWAY,
                ) from err

    async def undeploy(self, *, connector: Connector) -> None:
        async with self.api() as api:
            for resource_type, resource_name in (
                ("secret", f"managed-mcp-server-env-{connector.id.hex[:16]}"),
                ("deployment", f"managed-mcp-server-{connector.id.hex[:16]}"),
                ("deployment", f"managed-mcp-supergateway-{connector.id.hex[:16]}"),
                ("service", f"managed-mcp-supergateway-{connector.id.hex[:16]}"),
            ):
                try:
                    resource = None
                    if resource_type == "deployment":
                        resource = await Deployment.get(name=resource_name, api=api)
                    elif resource_type == "service":
                        resource = await Service.get(name=resource_name, api=api)
                    elif resource_type == "secret":
                        resource = await Secret.get(name=resource_name, api=api)
                    if resource:
                        await resource.delete()
                except Exception as err:
                    logger.warning("Failed to delete %s/%s: %s", resource_type, resource_name, err)
