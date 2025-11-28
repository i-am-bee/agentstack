# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging

from fastapi import status
from kink import inject

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

    def find_preset(self, *, connector: Connector) -> ConnectorPreset | None:
        return next((p for p in self._configuration.connector.presets if str(p.url) == str(connector.url)), None)

    def is_managed(self, *, connector: Connector) -> bool:
        return (preset := self.find_preset(connector=connector)) is not None and preset.url.scheme == "mcp+stdio"

    def get_service_url(self, *, connector: Connector) -> str:
        return f"http://managed-mcp-{connector.id.hex[:16]}.{self._kubectl._default_kwargs['namespace']}.svc.cluster.local:8080"

    async def deploy(self, *, connector: Connector) -> None:
        logger.info("Creating managed MCP deployment: connector_id=%s", connector.id)
        preset = self.find_preset(connector=connector)
        assert preset and preset.stdio

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
                                "name": f"managed-mcp-{connector.id.hex[:16]}",
                                "labels": {
                                    "app": "managed-mcp",
                                    "connector-id": str(connector.id),
                                },
                            },
                            "spec": {
                                "replicas": 1,
                                "selector": {
                                    "matchLabels": {
                                        "app": "managed-mcp",
                                        "connector-id": str(connector.id),
                                    }
                                },
                                "template": {
                                    "metadata": {
                                        "labels": {
                                            "app": "managed-mcp",
                                            "connector-id": str(connector.id),
                                        }
                                    },
                                    "spec": {
                                        "serviceAccountName": "managed-mcp",
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
                                                    else {
                                                        "env": [
                                                            {"name": k, "value": v} for k, v in preset.stdio.env.items()
                                                        ]
                                                    }
                                                ),
                                            },
                                            {
                                                "name": "supergateway",
                                                "image": "ghcr.io/i-am-bee/agentstack/agentstack-server:local",
                                                "command": ["supergateway"],
                                                "args": [
                                                    "--stdio",
                                                    "kubectl attach $(POD_NAME) -c mcp-server --stdin --tty=false",
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
                                                "env": [
                                                    {
                                                        "name": "POD_NAME",
                                                        "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}},
                                                    }
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
                            "metadata": {"name": f"managed-mcp-{connector.id.hex[:16]}"},
                            "spec": {
                                "selector": {
                                    "app": "managed-mcp",
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
            logger.info("MCP server deployment created: connector_id=%s", connector.id)
        except RuntimeError as err:
            raise PlatformError(
                f"Failed to create MCP server deployment: {err}",
                status_code=status.HTTP_502_BAD_GATEWAY,
            ) from err

        logger.info("Waiting for deployment to be ready: connector_id=%s", connector.id)

        try:
            await self._kubectl.wait(
                f"deployment/managed-mcp-{connector.id.hex[:16]}",
                _for="condition=Available",
                timeout="60s",
            )
        except RuntimeError as err:
            raise PlatformError(
                "Managed MCP deployment failed to become ready",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            ) from err

        logger.info(
            "Managed MCP server deployment ready: connector_id=%s url=%s",
            connector.id,
            self.get_service_url(connector=connector),
        )

    async def undeploy(self, *, connector: Connector) -> None:
        logger.info("Deleting managed MCP server deployment: connector_id=%s", connector.id)

        for resource_type in ["deployment", "service"]:
            try:
                await self._kubectl.delete(resource_type, f"managed-mcp-{connector.id.hex[:16]}", ignore_not_found=True)
            except RuntimeError as err:
                logger.warning("Failed to delete %s/managed-mcp-%s: %s", resource_type, connector.id.hex[:16], err)

        logger.info("Managed MCP server deployment deployment deleted: connector_id=%s", connector.id)
