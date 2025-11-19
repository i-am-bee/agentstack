# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import html
import logging
from contextlib import AsyncExitStack
from datetime import timedelta
from secrets import token_urlsafe
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from uuid import UUID

import httpx
from async_lru import alru_cache
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata, get_well_known_url
from fastapi import Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from kink import inject
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import AnyUrl, BaseModel

from agentstack_server.configuration import Configuration, ConnectorPreset
from agentstack_server.domain.models.common import Metadata
from agentstack_server.domain.models.connector import (
    Authorization,
    AuthorizationCodeFlow,
    Connector,
    ConnectorState,
    Token,
)
from agentstack_server.domain.models.user import User
from agentstack_server.exceptions import EntityNotFoundError, PlatformError
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ConnectorService:
    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration):
        self._uow = uow
        self._configuration = configuration
        self._proxy_client = httpx.AsyncClient(timeout=None)

    async def create_connector(
        self,
        *,
        user: User,
        url: AnyUrl,
        client_id: str | None,
        client_secret: str | None,
        metadata: Metadata | None,
        match_preset: bool = True,
    ) -> Connector:
        if client_secret and not client_id:
            raise PlatformError(
                "client_id must be present when client_secret is specified", status_code=status.HTTP_400_BAD_REQUEST
            )

        preset = self._find_preset(url=url) if match_preset else None
        if not preset and url.scheme not in {"http", "https"}:
            raise PlatformError("Unknown connector preset", status_code=status.HTTP_400_BAD_REQUEST)

        if preset:
            if not client_id:
                client_id = preset.client_id
                client_secret = preset.client_secret
            metadata = metadata or preset.metadata

        connector = Connector(
            url=url,
            created_by=user.id,
            auth=Authorization(client_id=client_id, client_secret=client_secret) if client_id else None,
            metadata=metadata,
        )
        async with self._uow() as uow:
            await uow.connectors.create(connector=connector)
            await uow.commit()

        # For stdio connectors, create the supergateway pod immediately
        if preset and str(preset.url).startswith("mcp+stdio://"):
            logger.info("Creating supergateway pod for stdio connector: connector_id=%s", connector.id)
            try:
                await self._create_supergateway_pod(connector=connector, preset=preset)
            except Exception as err:
                logger.error("Failed to create supergateway pod during connector creation", exc_info=True)
                # Delete the connector from DB since we couldn't create the pod
                async with self._uow() as uow:
                    await uow.connectors.delete(connector_id=connector.id, user_id=user.id)
                    await uow.commit()
                raise PlatformError(
                    f"Failed to create stdio connector: {err}",
                    status_code=status.HTTP_502_BAD_GATEWAY,
                ) from err

        return connector

    async def read_connector(self, *, connector_id: UUID, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            return await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

    async def delete_connector(self, *, connector_id: UUID, user: User | None = None) -> None:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)
            await self._revoke_auth_token(connector=connector)

            # For stdio connectors, delete the supergateway pod
            preset = self._find_preset(url=connector.url)
            if preset and str(preset.url).startswith("mcp+stdio://"):
                try:
                    await self._delete_supergateway_pod(connector=connector)
                except Exception:
                    logger.warning("Failed to delete supergateway pod during connector deletion", exc_info=True)

            await uow.connectors.delete(connector_id=connector_id, user_id=user.id if user else None)
            await uow.commit()

    async def list_connectors(self, *, user: User | None = None) -> list[Connector]:
        async with self._uow() as uow:
            return [c async for c in uow.connectors.list(user_id=user.id if user else None)]

    async def connect_connector(
        self, *, connector_id: UUID, callback_uri: str, redirect_url: AnyUrl | None = None, user: User | None = None
    ) -> Connector:
        logger.error("Connecting connector: connector_id=%s url=%s", connector_id, "unknown")
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        logger.error("Connector retrieved: connector_id=%s url=%s", connector_id, connector.url)

        # For stdio connectors, skip probing since pods are already created and running
        # Probing causes the supergateway to crash due to connection state issues
        preset = self._find_preset(url=connector.url)
        is_stdio_connector = preset and str(preset.url).startswith("mcp+stdio://")

        try:
            if is_stdio_connector:
                logger.info("Skipping probe for stdio connector: connector_id=%s", connector_id)
                connector.state = ConnectorState.connected
                connector.disconnect_reason = None
            else:
                logger.error("Probing connector: connector_id=%s", connector_id)
                await self.probe_connector(connector=connector)
                logger.error("Connector probe successful: connector_id=%s", connector_id)
                connector.state = ConnectorState.connected
                connector.disconnect_reason = None
        except Exception as err:
            if isinstance(err, httpx.HTTPStatusError):
                if err.response.status_code == status.HTTP_401_UNAUTHORIZED:
                    await self._bootstrap_auth(
                        connector=connector, callback_url=callback_uri, redirect_url=redirect_url
                    )
                    connector.state = ConnectorState.auth_required
                else:
                    logger.error("Connector failed", exc_info=True)
                    try:
                        error = (await err.response.aread()).decode(err.response.encoding or "utf-8")
                    except Exception:
                        error = "Connector has returned an error"
                    raise PlatformError(
                        error,
                        status_code=status.HTTP_502_BAD_GATEWAY,
                    ) from err
            elif isinstance(err, httpx.RequestError):
                logger.error("Connector failed", exc_info=True)
                raise PlatformError(
                    "Unable to establish connection with the connector",
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                ) from err
            else:
                logger.error("Connector failed", exc_info=True)
                raise PlatformError("Connection has failed") from err

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def disconnect_connector(self, *, connector_id: UUID, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state not in (ConnectorState.connected, ConnectorState.disconnected, ConnectorState.auth_required):
            raise PlatformError(
                "Connector must be in connected, disconnected or auth_required state",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        await self._revoke_auth_token(connector=connector)

        # For stdio connectors, delete the supergateway pod
        preset = self._find_preset(url=connector.url)
        if preset and str(preset.url).startswith("mcp+stdio://"):
            try:
                await self._delete_supergateway_pod(connector=connector)
            except Exception:
                logger.warning("Failed to delete supergateway pod during disconnect", exc_info=True)

        if connector.auth:
            connector.auth.flow = None
        connector.state = ConnectorState.disconnected
        connector.disconnect_reason = "Client request"

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def oauth_callback(self, *, callback_url: str, state: str, error: str | None, error_description: str | None):
        redirect_url = None
        try:
            async with self._uow() as uow:
                connector = await uow.connectors.get_by_auth(auth_state=state)

            assert connector.auth is not None
            assert connector.auth.flow is not None
            assert connector.auth.flow.type == "code"

            redirect_url = connector.auth.flow.client_redirect_uri

            if error:
                return self._create_callback_response(
                    redirect_url=redirect_url, error=error, error_description=error_description
                )

            if connector.state not in (ConnectorState.auth_required):
                return self._create_callback_response(
                    redirect_url=redirect_url,
                    error="invalid_request",
                    error_description="Connector must be in auth_required state.",
                )

            async with self._create_oauth_client(connector=connector) as client:
                auth_metadata = await self._discover_auth_metadata(connector=connector)
                if not auth_metadata:
                    raise RuntimeError("Authorization server no longer contains necessary metadata")
                token_endpoint = auth_metadata.get("token_endpoint")
                if not token_endpoint:
                    raise RuntimeError("Authorization server has no token endpoint in metadata")
                token = await client.fetch_token(
                    token_endpoint,
                    authorization_response=callback_url,
                    code_verifier=connector.auth.flow.code_verifier,
                    redirect_uri=connector.auth.flow.redirect_uri,
                )
                connector.auth.token = Token.model_validate(token)
                connector.auth.token_endpoint = AnyUrl(str(token_endpoint))
                connector.auth.flow = None
            try:
                await self.probe_connector(connector=connector)
                connector.state = ConnectorState.connected
            except Exception as err:
                logger.error("Failed to probe resource with a valid token", exc_info=True)
                connector.state = ConnectorState.disconnected
                connector.disconnect_reason = str(err)

            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

            return self._create_callback_response(redirect_url=redirect_url)
        except EntityNotFoundError:
            return self._create_callback_response(
                redirect_url=redirect_url,
                error="invalid_request",
                error_description="Invalid or expired login attempt.",
            )
        except Exception:
            logger.error("oAuth callback failed", exc_info=True)
            return self._create_callback_response(
                redirect_url=redirect_url,
                error="server_error",
                error_description="An internal error has occurred. Please try again later.",
            )

    def _create_callback_response(
        self, *, redirect_url: AnyUrl | None, error: str | None = None, error_description: str | None = None
    ):
        if redirect_url:
            if error:
                parsed = urlparse(str(redirect_url))
                query_params = parse_qs(parsed.query)
                query_params["error"] = [error]
                if error_description:
                    query_params["error_description"] = [error_description]
                modified_url = urlunparse(parsed._replace(query=urlencode(query_params, doseq=True)))
                redirect_url = AnyUrl(modified_url)
            return RedirectResponse(str(redirect_url))
        else:
            return HTMLResponse(
                _render_success() if not error else _render_failure(error, error_description=error_description)
            )

    async def refresh_connector(self, *, connector_id: UUID, user: User | None = None) -> None:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state not in (ConnectorState.connected, ConnectorState.disconnected):
            return

        try:
            await self.probe_connector(connector=connector)
            connector.state = ConnectorState.connected
            connector.disconnect_reason = None
        except Exception as err:
            if isinstance(err, httpx.HTTPStatusError) and err.response.status_code == status.HTTP_401_UNAUTHORIZED:
                await self._revoke_auth_token(connector=connector)
                if connector.auth:
                    connector.auth.flow = None
            connector.state = ConnectorState.disconnected
            connector.disconnect_reason = str(err)
        finally:
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

    async def list_presets(self) -> list[ConnectorPreset]:
        return self._configuration.connector.presets

    def _find_preset(self, *, url: AnyUrl) -> ConnectorPreset | None:
        for preset in self._configuration.connector.presets:
            if str(preset.url) == str(url):
                return preset
        return None

    def _get_supergateway_name(self, connector_id: UUID) -> str:
        """Get DNS-safe name for supergateway pod/service."""
        return f"supergateway-{connector_id.hex[:8]}"

    def _get_supergateway_url(self, connector_id: UUID) -> str:
        """Get the service URL for an existing supergateway pod."""
        name = self._get_supergateway_name(connector_id)
        namespace = self._configuration.connector.runtime.namespace or self._configuration.k8s_namespace or "default"
        return f"http://{name}.{namespace}.svc.cluster.local:8080"

    async def _ensure_supergateway_rbac(self) -> None:
        """Ensure RBAC resources exist for supergateway pods."""
        namespace = self._configuration.connector.runtime.namespace or self._configuration.k8s_namespace or "default"
        kubeconfig = self._configuration.connector.runtime.kubeconfig or self._configuration.k8s_kubeconfig

        kubectl_args = ["kubectl"]
        if kubeconfig:
            kubectl_args.extend(["--kubeconfig", str(kubeconfig)])
        if namespace:
            kubectl_args.extend(["--namespace", namespace])

        # Create ServiceAccount, Role, and RoleBinding for supergateway
        rbac_yaml = f"""
apiVersion: v1
kind: ServiceAccount
metadata:
  name: supergateway
  namespace: {namespace or "default"}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: supergateway
  namespace: {namespace or "default"}
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["create", "delete", "get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
- apiGroups: [""]
  resources: ["pods/attach"]
  verbs: ["create", "get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: supergateway
  namespace: {namespace or "default"}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: supergateway
subjects:
- kind: ServiceAccount
  name: supergateway
  namespace: {namespace or "default"}
"""

        process = await asyncio.create_subprocess_exec(
            *kubectl_args,
            "apply",
            "-f",
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(input=rbac_yaml.encode())

        if process.returncode != 0:
            logger.error(
                "Failed to create supergateway RBAC resources: returncode=%s stdout=%s stderr=%s",
                process.returncode,
                stdout.decode(),
                stderr.decode(),
            )
            raise RuntimeError(f"Failed to create RBAC: {stderr.decode()}")
        else:
            logger.info("RBAC resources created successfully: %s", stdout.decode())

    async def _create_supergateway_pod(self, *, connector: Connector, preset: ConnectorPreset) -> str:
        """Create supergateway pod and service for stdio connector using kubectl."""
        logger.info("Creating supergateway pod: connector_id=%s", connector.id)

        # Ensure RBAC exists first
        await self._ensure_supergateway_rbac()

        name = self._get_supergateway_name(connector.id)
        namespace = self._configuration.connector.runtime.namespace or self._configuration.k8s_namespace or "default"
        kubeconfig = self._configuration.connector.runtime.kubeconfig or self._configuration.k8s_kubeconfig

        # Build kubectl command args
        kubectl_args = ["kubectl"]
        if kubeconfig:
            kubectl_args.extend(["--kubeconfig", str(kubeconfig)])
        if namespace:
            kubectl_args.extend(["--namespace", namespace])

        # Create MCP server pod name (one pod per connector, not per request)
        mcp_pod_name = f"conn-{connector.id.hex[:6]}-mcp"

        # Build kubectl attach command for supergateway to connect to the MCP pod
        kubectl_attach_cmd = f"kubectl attach {mcp_pod_name} --stdin --tty=false"

        # Build MCP pod command/args/env sections
        mcp_command_yaml = ""
        if preset.stdio.command:
            command_items = "\n    - ".join(f'"{cmd}"' for cmd in preset.stdio.command)
            mcp_command_yaml = f"\n    command:\n    - {command_items}"

        mcp_args_yaml = ""
        if preset.stdio.args:
            args_items = "\n    - ".join(f'"{arg}"' for arg in preset.stdio.args)
            mcp_args_yaml = f"\n    args:\n    - {args_items}"

        mcp_env_yaml = ""
        if preset.stdio.env:
            env_items = "\n    - ".join(f'name: "{k}"\n      value: "{v}"' for k, v in preset.stdio.env.items())
            mcp_env_yaml = f"\n    env:\n    - {env_items}"

        # Create manifest YAML for MCP server pod, supergateway pod, and service
        # TODO: Make supergateway image configurable
        pod_yaml = f"""
apiVersion: v1
kind: Pod
metadata:
  name: {mcp_pod_name}
  labels:
    app: mcp-server
    connector-id: "{connector.id}"
spec:
  serviceAccountName: supergateway
  restartPolicy: Never
  containers:
  - name: mcp
    image: {preset.stdio.image}
    imagePullPolicy: IfNotPresent
    stdin: true
    tty: false{mcp_command_yaml}{mcp_args_yaml}{mcp_env_yaml}
---
apiVersion: v1
kind: Pod
metadata:
  name: {name}
  labels:
    app: supergateway
    connector-id: "{connector.id}"
spec:
  serviceAccountName: supergateway
  containers:
  - name: supergateway
    image: ghcr.io/i-am-bee/agentstack/agentstack-server:local
    command: ["supergateway"]
    args:
    - "--stdio"
    - "{kubectl_attach_cmd}"
    - "--outputTransport"
    - "streamableHttp"
    - "--stateful"
    - "--port"
    - "8080"
    - "--streamableHttpPath"
    - "/mcp"
    - "--logLevel"
    - "info"
    ports:
    - containerPort: 8080
      protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
spec:
  selector:
    app: supergateway
    connector-id: "{connector.id}"
  ports:
  - name: http
    port: 8080
    targetPort: 8080
    protocol: TCP
"""

        # Apply manifest
        process = await asyncio.create_subprocess_exec(
            *kubectl_args,
            "apply",
            "-f",
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(input=pod_yaml.encode())

        if process.returncode != 0:
            raise PlatformError(
                f"Failed to create supergateway pod: {stderr.decode()}",
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        logger.info("Supergateway resources created: connector_id=%s output=%s", connector.id, stdout.decode().strip())
        logger.info("Waiting for MCP server and supergateway pods to be ready: connector_id=%s", connector.id)

        # Wait for MCP server pod to be ready first
        wait_mcp_process = await asyncio.create_subprocess_exec(
            *kubectl_args,
            "wait",
            f"pod/{mcp_pod_name}",
            "--for=condition=Ready",
            f"--timeout={self._configuration.connector.runtime.startup_timeout_seconds}s",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await wait_mcp_process.wait()

        if wait_mcp_process.returncode != 0:
            raise PlatformError(
                "MCP server pod failed to become ready",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        # Wait for supergateway pod to be ready
        wait_gw_process = await asyncio.create_subprocess_exec(
            *kubectl_args,
            "wait",
            f"pod/{name}",
            "--for=condition=Ready",
            f"--timeout={self._configuration.connector.runtime.startup_timeout_seconds}s",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await wait_gw_process.wait()

        if wait_gw_process.returncode != 0:
            raise PlatformError(
                "Supergateway pod failed to become ready",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        service_url = f"http://{name}.{namespace}.svc.cluster.local:8080"
        logger.info("Supergateway pod ready: connector_id=%s url=%s", connector.id, service_url)

        return service_url

    async def _delete_supergateway_pod(self, *, connector: Connector) -> None:
        """Delete supergateway pod, MCP server pod, and service using kubectl."""
        logger.info("Deleting supergateway and MCP server pods: connector_id=%s", connector.id)

        name = self._get_supergateway_name(connector.id)
        mcp_pod_name = f"conn-{connector.id.hex[:6]}-mcp"
        namespace = self._configuration.connector.runtime.namespace or self._configuration.k8s_namespace or "default"
        kubeconfig = self._configuration.connector.runtime.kubeconfig or self._configuration.k8s_kubeconfig

        kubectl_args = ["kubectl"]
        if kubeconfig:
            kubectl_args.extend(["--kubeconfig", str(kubeconfig)])
        if namespace:
            kubectl_args.extend(["--namespace", namespace])

        # Delete supergateway pod, MCP server pod, and service
        for resource_type, resource_name in [("pod", name), ("pod", mcp_pod_name), ("service", name)]:
            process = await asyncio.create_subprocess_exec(
                *kubectl_args,
                "delete",
                resource_type,
                resource_name,
                "--ignore-not-found=true",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()

        logger.info("Supergateway and MCP server pods deleted: connector_id=%s", connector.id)

    async def _bootstrap_auth(self, *, connector: Connector, callback_url: str, redirect_url: AnyUrl | None) -> None:
        auth_metadata = await self._discover_auth_metadata(connector=connector)
        if not auth_metadata:
            raise RuntimeError("Not authorization server found for the connector")

        if not connector.auth:
            connector.auth = Authorization()

        await self._revoke_auth_token(connector=connector)
        code_verifier = token_urlsafe(64)

        await self._ensure_oauth_client_registered(connector=connector, redirect_uri=callback_url)

        async with self._create_oauth_client(connector=connector) as client:
            uri, state = client.create_authorization_url(
                auth_metadata.get("authorization_endpoint"), code_verifier=code_verifier, redirect_uri=callback_url
            )
            connector.auth.flow = AuthorizationCodeFlow(
                authorization_endpoint=uri,
                state=state,
                code_verifier=code_verifier,
                redirect_uri=callback_url,
                client_redirect_uri=redirect_url,
            )

    async def _revoke_auth_token(self, *, connector: Connector) -> None:
        if not connector.auth or not connector.auth.token:
            return

        if connector.auth.token:
            try:
                async with self._create_oauth_client(connector=connector) as client:
                    auth_metadata = await self._discover_auth_metadata(connector=connector)
                    if not auth_metadata:
                        raise RuntimeError("Authorization server no longer contains necessary metadata")
                    revoke_endpoint = auth_metadata.get("revocation_endpoint")
                    if not isinstance(revoke_endpoint, str):
                        raise RuntimeError("Authorization server does not support token revocation")
                    await client.revoke_token(revoke_endpoint, token=connector.auth.token.access_token)
            except Exception:
                logger.warning("Token revocation failed", exc_info=True)

            connector.auth.token = None
            connector.auth.token_endpoint = None
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

    def _create_client(
        self, *, connector: Connector, headers: dict[str, str] | None = None, timeout: int | None = None
    ) -> httpx.AsyncClient:
        if not connector.auth or not connector.auth.token:
            return httpx.AsyncClient(
                headers=headers,
                timeout=timeout or 30,
                base_url="" if (url := str(connector.url)).startswith("mcp+stdio://") else url,
            )
        else:
            return self._create_oauth_client(connector=connector)

    def _create_oauth_client(
        self, *, connector: Connector, headers: dict[str, str] | None = None, timeout: int | None = None
    ) -> AsyncOAuth2Client:
        if not connector.auth:
            raise RuntimeError("Connector does not support auth")

        async def update_token(token, refresh_token=None, access_token=None):
            if not connector.auth:
                raise RuntimeError("Authorization has been removed from the connector")
            connector.auth.token = Token.model_validate(token)
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

        return AsyncOAuth2Client(
            client_id=connector.auth.client_id,
            client_secret=connector.auth.client_secret,
            token=connector.auth.token.model_dump() if connector.auth.token else None,
            update_token=update_token,
            code_challenge_method="S256",
            headers=headers,
            timeout=timeout,
            leeway=60,  # A job probes connectors every 30 seconds, ensuring the token is valid roughly for at least 30 seconds per request.
            token_endpoint=str(connector.auth.token_endpoint),
        )

    async def _discover_auth_metadata(self, *, connector: Connector) -> AuthorizationServerMetadata | None:
        resource_metadata = await _discover_resource_metadata(str(connector.url))
        if not resource_metadata or not resource_metadata.authorization_servers:
            return None
        auth_metadata = await _discover_auth_metadata(resource_metadata.authorization_servers[0])
        return auth_metadata

    async def _ensure_oauth_client_registered(self, *, connector: Connector, redirect_uri: str) -> Connector:
        if not connector.auth:
            raise RuntimeError("Authoriztion hasn't been activated for connector")
        if not connector.auth.client_id:
            registration_response = await _register_client(str(connector.url), redirect_uri=redirect_uri)
            async with self._uow() as uow:
                connector.auth.client_id = registration_response.client_id
                connector.auth.client_secret = registration_response.client_secret
                await uow.connectors.update(connector=connector)
                await uow.commit()
        return connector

    async def probe_connector(self, *, connector: Connector):
        def client_factory(headers=None, timeout=None, auth=None):
            assert auth is None
            return self._create_client(connector=connector, headers=headers, timeout=timeout)

        # Determine target URL
        preset = self._find_preset(url=connector.url)
        if preset and str(preset.url).startswith("mcp+stdio://"):
            # Use existing supergateway pod service URL
            target_url = f"{self._get_supergateway_url(connector.id)}/mcp"
        else:
            # Regular HTTP connector
            target_url = str(connector.url)

        logger.info("Probing connector: connector_id=%s target_url=%s", connector.id, target_url)

        try:
            async with AsyncExitStack() as stack:
                read, write, _ = await stack.enter_async_context(
                    streamablehttp_client(target_url, httpx_client_factory=client_factory)
                )
                session = await stack.enter_async_context(ClientSession(read, write))
                async with asyncio.timeout(30):
                    await session.initialize()
            logger.info("Connector probe successful: connector_id=%s", connector.id)
        except TimeoutError as err:
            logger.error(
                "Connector probe timed out: connector_id=%s target_url=%s", connector.id, target_url, exc_info=True
            )
            raise PlatformError(
                "MCP server initialization timed out",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            ) from err
        except ExceptionGroup as excgroup:
            logger.error(
                "Connector probe failed with ExceptionGroup: connector_id=%s target_url=%s exceptions=%s",
                connector.id,
                target_url,
                excgroup.exceptions,
                exc_info=True,
            )
            if len(excgroup.exceptions) == 1:
                raise excgroup.exceptions[0] from excgroup
            raise excgroup
        except Exception as err:
            logger.error(
                "Connector probe failed: connector_id=%s target_url=%s error=%s",
                connector.id,
                target_url,
                err,
                exc_info=True,
            )
            raise

    async def mcp_proxy(self, *, connector_id: UUID, request: Request, user: User | None = None):
        connector = await self.read_connector(connector_id=connector_id, user=user)
        preset = self._find_preset(url=connector.url)

        forward_headers = {
            key: request.headers[key]
            for key in ["accept", "content-type", "mcp-protocol-version", "mcp-session-id", "last-event-id"]
            if key in request.headers
        }

        # Determine target URL
        if preset and str(preset.url).startswith("mcp+stdio://"):
            # Use existing supergateway pod service URL
            target_url = f"{self._get_supergateway_url(connector.id)}/mcp"
        else:
            # Regular HTTP connector
            target_url = str(connector.url)

        exit_stack = AsyncExitStack()
        try:
            response = await exit_stack.enter_async_context(
                self._proxy_client.stream(
                    request.method,
                    target_url,
                    headers=forward_headers
                    | (
                        {"authorization": f"Bearer {connector.auth.token.access_token}"}
                        if connector.state == ConnectorState.connected
                        and connector.auth
                        and connector.auth.token
                        and connector.auth.token.token_type == "bearer"
                        else {}
                    ),
                    content=request.stream(),
                )
            )

            async def stream_fn():
                try:
                    async for chunk in response.aiter_bytes():
                        yield chunk
                finally:
                    await exit_stack.pop_all().aclose()

            return StreamingResponse(stream_fn(), status_code=response.status_code, headers=response.headers)
        except BaseException:
            await exit_stack.pop_all().aclose()
            raise


@alru_cache(ttl=timedelta(days=1).seconds)
async def _register_client(resource_server_url: str, *, redirect_uri: str) -> _ClientRegistrationResponse:
    resource_metadata = await _discover_resource_metadata(resource_server_url)
    if not resource_metadata or not resource_metadata.authorization_servers:
        raise RuntimeError("Resource server metadata not found")
    auth_metadata = await _discover_auth_metadata(resource_metadata.authorization_servers[0])
    if not auth_metadata:
        raise RuntimeError("Authorization server metadata not found")
    registration_endpoint = auth_metadata.get("registration_endpoint")
    if not isinstance(registration_endpoint, str):
        raise RuntimeError("Authorization server does not support dynamic client registration")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            str(registration_endpoint),
            json={"client_name": "Agent Stack", "redirect_uris": [redirect_uri]},
        )
        response.raise_for_status()
        registration_response = _ClientRegistrationResponse.model_validate(response.json())
        return registration_response


@alru_cache(ttl=timedelta(minutes=10).seconds)
async def _discover_auth_metadata(authorization_server_url: str) -> AuthorizationServerMetadata | None:
    url = get_well_known_url(authorization_server_url, external=True)
    async with httpx.AsyncClient(headers={"Accept": "application/json"}, follow_redirects=True) as client:
        response = await client.get(url)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None
        response.raise_for_status()
        metadata = AuthorizationServerMetadata(response.json())
        metadata.validate()
        return metadata


@alru_cache(ttl=timedelta(minutes=10).seconds)
async def _discover_resource_metadata(resource_url: str) -> _ResourceServerMetadata | None:
    parsed = urlparse(resource_url)
    resource_root_url = f"{parsed.scheme}://{parsed.netloc}"

    # RFC9728 hasn't been implemented yet in authlib
    # Reusing util from RFC8414
    path_url = get_well_known_url(resource_url, external=True, suffix="oauth-protected-resource")
    root_url = get_well_known_url(resource_root_url, external=True, suffix="oauth-protected-resource")
    urls = [path_url]
    if path_url != root_url:  # avoid duplicate
        urls.append(root_url)
    exceptions = []
    async with httpx.AsyncClient(
        headers={"Accept": "application/json"},
        follow_redirects=True,
    ) as client:
        for url in urls:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return _ResourceServerMetadata.model_validate(response.json())
            except Exception as exc:
                exceptions.append(exc)
    logger.warning(
        "Resource metadata discovery failed",
        exc_info=ExceptionGroup(f"Unable to discover metadata for resource {resource_url}", exceptions),
    )
    return None


def _render_success():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Stack</title>
  <style>
    body { font-family: system-ui, sans-serif; text-align: center; margin-top: 5rem; }
  </style>
</head>
<body>
  <h1 id="msg">Authorization Successful</h1>
  <p id="detail">You can now close this window and return to your application.</p>

  <script>
    // Auto-close after 8 seconds (best effort)
    setTimeout(() => window.close(), 8000);
  </script>
</body>
</html>"""


def _render_failure(error: str, error_description: str | None):
    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Stack</title>
  <style>
    body { font-family: system-ui, sans-serif; text-align: center; margin-top: 5rem; }
  </style>
</head>
<body>
  <h1 id="msg">Authorization Failed</h1>
  <p id="detail">"""
        + html.escape(error_description or error)
        + """</p>
</body>
</html>"""
    )


class _ResourceServerMetadata(BaseModel):
    authorization_servers: list[str]


class _ClientRegistrationResponse(BaseModel):
    client_id: str
    client_secret: str | None = None
