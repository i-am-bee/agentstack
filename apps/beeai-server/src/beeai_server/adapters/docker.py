# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import base64
import logging
import re
import uuid
from contextlib import asynccontextmanager, suppress, AsyncExitStack
from datetime import timedelta
from typing import Iterable, AsyncGenerator, AsyncIterator

import aiohttp
import anyio
import anyio.to_thread
from httpx import HTTPError as HttpxHTTPError
from aiodocker import Docker, DockerError
from aiohttp.web_exceptions import HTTPError as AioHTTPError
from httpx import AsyncClient
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_fixed, stop_after_delay

from beeai_server.adapters.interface import IContainerBackend
from beeai_server.configuration import Configuration, OCIRegistryConfiguration
from beeai_server.custom_types import ID
from beeai_server.domain.constants import DOCKER_MANIFEST_LABEL_NAME
from beeai_server.exceptions import retry_if_exception_grp_type
from beeai_server.utils.docker import DockerImageID, replace_localhost_url
from beeai_server.utils.github import ResolvedGithubUrl
from beeai_server.utils.logs_container import LogsContainer
from beeai_server.utils.process import find_free_port
from beeai_server.utils.utils import cancel_task, extract_messages

logger = logging.getLogger(__name__)


class DockerContainerBackend(IContainerBackend):
    def __init__(self, *, docker_host: str, configuration: Configuration) -> None:
        self.configuration = configuration
        self._docker_host = docker_host
        self._extra_hosts = []

    def _get_auth_header(self, destination: DockerImageID) -> dict | None:
        config: OCIRegistryConfiguration = self.configuration.oci_registry[destination.registry]
        return config.basic_auth_str and {"auth": config.basic_auth_str}

    async def configure_host_docker_internal(self):
        """Set extra_hosts if `host.docker.internal` is not configured for containers."""

        async with self._docker as docker:
            alpine = "alpine:3.21.3"
            try:
                await docker.images.inspect(alpine)
            except DockerError:
                await docker.images.pull(alpine)
            container = await docker.containers.create_or_replace(
                name="beeai-host-network-test",
                config={"Image": "alpine:3.21.3", "Cmd": ["getent", "hosts", "host.docker.internal"]},
            )
            await container.start()
            resp = await container.wait()
            if resp["StatusCode"] == 0:
                return
        logger.warning("host.docker.internal not configured for docker, falling back to 'host-gateway' configuration")
        self._extra_hosts = ["host.docker.internal:host-gateway"]

    async def import_image(self, *, data: AsyncIterator[bytes], image_id: DockerImageID):
        async with self._docker as docker:
            resp = await docker.images.import_image(data=data)
            if resp and "error" in resp[0]:
                raise DockerError(status=500, data={"message": resp[0]["error"]})
            [name] = re.findall(r"sha256:.*", resp[0]["stream"].strip())
            await docker.images.tag(name, repo=f"{image_id.registry}/{image_id.repository}", tag=image_id.tag)

    async def build_from_github(
        self,
        *,
        github_url: ResolvedGithubUrl,
        destination: DockerImageID | None = None,
        logs_container: LogsContainer | None = None,
    ) -> DockerImageID:
        logs_container = logs_container or LogsContainer()
        path = f":{github_url.path}" if github_url.path else ""
        tag = (
            str(destination)
            if destination
            else f"{github_url.org}/{github_url.repo}/{github_url.path}:{github_url.version}"
        )
        remote = f"https://github.com/{github_url.org}/{github_url.repo}.git#{github_url.version}{path}"
        tmp_image = uuid.uuid4().hex
        async with self._docker as docker:
            logs_container.add_stdout("ℹ️ Building image")
            async for message in docker.images.build(remote=remote, tag=tmp_image, stream=True):
                text = message["stream"] if "stream" in message else str(message)
                if text.strip():
                    logs_container.add_stdout(text)
            logs_container.add_stdout("ℹ️ Extracting agents")
            host_port = await find_free_port()
            container = await docker.containers.create_or_replace(
                name=tmp_image,
                config={
                    "Image": tmp_image,
                    "ExposedPorts": {"8000/tcp": {}},
                    "Env": ["HOST=0.0.0.0"],
                    "HostConfig": {
                        "PortBindings": {"8000/tcp": [{"HostIp": "0.0.0.0", "HostPort": str(host_port)}]},
                        "AutoRemove": True,
                    },
                },
            )
            try:
                await container.start()
                async for attempt in AsyncRetrying(
                    stop=stop_after_delay(timedelta(seconds=30)),
                    wait=wait_fixed(timedelta(seconds=0.5)),
                    retry=retry_if_exception_grp_type(HttpxHTTPError),
                    reraise=True,
                ):
                    with attempt:
                        async with AsyncClient() as client:
                            resp = await client.get(f"http://localhost:{host_port}/agents", timeout=1)
                labels = {DOCKER_MANIFEST_LABEL_NAME: base64.b64encode(resp.content).decode()}
                logs_container.add_stdout("ℹ️ Adding extracted labels to image")
                await docker.images.build(remote=remote, tag=tag, labels=labels)
                logs_container.add_stdout(f"✅ Successfully built image: {tag}")
            except Exception as e:
                message = f"Error when extracting labels out of image: {extract_messages(e)}"
                logger.error(message, exc_info=e)
                logs_container.add_stderr(message)
                raise e
            finally:
                with suppress(DockerError):
                    await container.delete(force=True)

        return DockerImageID(root=tag)

    async def check_image(self, *, image: DockerImageID | str) -> bool:
        async with self._docker as docker:
            with suppress(DockerError):
                await docker.images.inspect(str(image))
                return True
            return False

    async def extract_labels(self, *, image: DockerImageID) -> dict[str, str]:
        async with self._docker as docker:
            image_info = await docker.images.inspect(str(image))
            return image_info["Config"]["Labels"]

    async def delete_image(self, *, image: DockerImageID):
        async with self._docker as docker:
            await docker.images.delete(str(image), force=True)

    async def pull_image(
        self, *, image: DockerImageID, logs_container: LogsContainer | None = None, force: bool = False
    ):
        async with self._docker as docker:
            with suppress(DockerError):
                await docker.images.inspect(str(image))
                return  # image already exists
            if logs_container:
                progress = {}
                async for message in docker.pull(str(image), auth=self._get_auth_header(image), stream=True):
                    status = message["status"]
                    if progress_detail := message.get("progressDetail", None):
                        id = message["id"]
                        if (id, status) not in progress:
                            logs_container.add_stdout(f"{id}: {status}")
                        progress[(id, status)] = progress_detail
                    else:
                        id_msg = f"{message['id']}: " if "id" in message else ""
                        logs_container.add_stdout(f"{id_msg}{status}")
            else:
                await docker.pull(str(image), auth=self._get_auth_header(image))

    @property
    def _docker(self) -> Docker:
        docker = Docker(self._docker_host, session=AsyncExitStack())
        return Docker(
            url=self._docker_host,
            session=aiohttp.ClientSession(connector=docker.connector, timeout=aiohttp.ClientTimeout(sock_connect=30)),
        )

    async def stream_logs(self, container_id: ID, logs_container: LogsContainer):
        async for attempt in AsyncRetrying(retry=retry_if_exception_type(AioHTTPError), reraise=True):
            with attempt:
                async with self._docker as docker:
                    container = await docker.containers.get(container_id)
                    async for log_message in container.log(stdout=True, stderr=True, follow=True):
                        if log_message.strip():
                            logs_container.add_stdout(log_message)

    @asynccontextmanager
    async def open_container(
        self,
        *,
        image: DockerImageID,
        name: str | None = None,
        command: list[str] | None = None,
        volumes: Iterable[str] | None = None,
        env: dict[str, str] | None = None,
        port_mappings: dict[str, str] | None = None,
        logs_container: LogsContainer | None = None,
        restart: str | None = None,
    ) -> AsyncGenerator[ID, None]:
        # Dirty networking fix
        env = env or {}
        env = {key: replace_localhost_url(val) for key, val in env.items()}

        container_id = None
        logs_streaming_task = None

        try:
            async with self._docker as docker:
                name = name or image.repository.replace("/", "-")
                config = {"Image": str(image), "HostConfig": {}}
                if self._extra_hosts:
                    config["HostConfig"]["ExtraHosts"] = self._extra_hosts
                if volumes:
                    config["HostConfig"]["Binds"] = list(volumes) or []
                if restart:
                    restart_type, count = (restart if ":" in restart else f"{restart}:0").split(":")
                    config["HostConfig"]["RestartPolicy"] = {"Name": restart_type, "MaximumRetryCount": int(count)}
                else:
                    config["HostConfig"]["AutoRemove"] = True
                if env:
                    config["Env"] = [f"{var}={value}" for var, value in env.items()]
                if command:
                    config["Cmd"] = command
                if port_mappings:
                    config["ExposedPorts"] = {f"{port}/tcp": {} for port in port_mappings.values()}
                    config["HostConfig"]["PortBindings"] = {
                        f"{container_port}/tcp": [{"HostIp": "0.0.0.0", "HostPort": str(host_port)}]
                        for host_port, container_port in port_mappings.items()
                    }
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(5),
                    wait=wait_fixed(1),
                    retry=retry_if_exception_type(DockerError),
                    reraise=True,
                ):
                    with attempt:
                        container = await docker.containers.create_or_replace(name=name, config=config)
                        await container.start()
                        container_id = container.id
                if logs_container:
                    logs_streaming_task = asyncio.create_task(self.stream_logs(container_id, logs_container))
                yield container_id
        finally:
            with anyio.CancelScope(shield=True):
                if container_id:
                    await cancel_task(logs_streaming_task)
                    async with self._docker as docker:
                        with suppress(DockerError):
                            container = await docker.containers.get(container_id)
                            await container.delete(force=True)
