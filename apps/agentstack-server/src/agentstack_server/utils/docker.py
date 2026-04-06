# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import hashlib
import re
from datetime import timedelta
from enum import StrEnum
from functools import cached_property
from typing import Any, NamedTuple

import httpx
from async_lru import alru_cache
from kink import di
from pydantic import (
    BaseModel,
    ConfigDict,
    ModelWrapValidatorHandler,
    PrivateAttr,
    RootModel,
    computed_field,
    model_validator,
)

from agentstack_server.configuration import Configuration, OCIRegistryConfiguration


class RegistryPermissions(StrEnum):
    PULL = "pull"
    PUSH = "push"


class RegistryAuthScheme(StrEnum):
    BEARER = "bearer"
    BASIC = "basic"


class RegistryAuthInfo(NamedTuple):
    scheme: RegistryAuthScheme
    token_url: str | None  # None for Basic auth registries


AUTH_URL_PER_REGISTRY: dict[str, RegistryAuthInfo] = {
    "ghcr.io": RegistryAuthInfo(
        RegistryAuthScheme.BEARER,
        "https://ghcr.io/token?service=ghcr.io&scope=repository:{repository}:{permissions}",
    ),
    "icr.io": RegistryAuthInfo(
        RegistryAuthScheme.BEARER,
        "https://icr.io/oauth/token?service=registry&scope=repository:{repository}:{permissions}",
    ),
    "us.icr.io": RegistryAuthInfo(
        RegistryAuthScheme.BEARER,
        "https://us.icr.io/oauth/token?service=registry&scope=repository:{repository}:{permissions}",
    ),
    "docker.io": RegistryAuthInfo(
        RegistryAuthScheme.BEARER,
        "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repository}:{permissions}",
    ),
    "registry-1.docker.io": RegistryAuthInfo(
        RegistryAuthScheme.BEARER,
        "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repository}:{permissions}",
    ),
}

base_headers = {
    "Accept": (
        "application/vnd.oci.image.index.v1+json,"
        "application/vnd.oci.image.manifest.v1+json,"
        "application/vnd.docker.distribution.manifest.list.v2+json,"
        "application/vnd.docker.distribution.manifest.v2+json"
    )
}


class ManifestResponse(NamedTuple):
    manifest: dict[str, Any]
    digest: str


class DockerImageID(RootModel[str]):
    model_config = ConfigDict(frozen=True)

    _registry: str | None = PrivateAttr(None)
    _repository: str = PrivateAttr()
    _tag: str | None = PrivateAttr(None)
    _digest: str | None = PrivateAttr(None)
    _manifest: dict[str, Any] | None = PrivateAttr(None)

    @property
    def registry_config(self) -> OCIRegistryConfiguration:
        return di[Configuration].oci_registry[self.registry]

    @cached_property
    def registry_base_url(self) -> str:
        registry = self.registry

        if registry.endswith("docker.io"):
            registry = "registry-1.docker.io"
        return f"{self.registry_config.protocol}://{registry}"

    @cached_property
    def manifest_base_url(self) -> str:
        return f"{self.registry_base_url}/v2/{self.repository}/manifests"

    @cached_property
    def get_manifest_url(self) -> str:
        version = self.digest or self.tag
        return f"{self.manifest_base_url}/{version}"

    @property
    def registry(self) -> str:
        return self._registry or "docker.io"

    @property
    def repository(self) -> str:
        if self.registry.endswith("docker.io") and "/" not in self._repository:
            return f"library/{self._repository}"
        return self._repository

    @property
    def base(self) -> str:
        return f"{self.registry}/{self.repository}"

    @property
    def tag(self) -> str:
        return self._tag or "latest"

    @property
    def digest(self) -> str | None:
        return self._digest or None

    @model_validator(mode="wrap")
    @classmethod
    def _parse(cls, data: Any, handler: ModelWrapValidatorHandler):
        if isinstance(data, DockerImageID):
            return data
        if not isinstance(data, str):
            raise ValueError(f"Invalid Docker image: {data}")

        pattern = r"""
            # Forbid starting with http:// or https://
            ^(?!https?://)

            # Registry (optional) - ends with slash and contains at least one dot
            # For local registries, these must use the svc.namespace url pattern, otherwise we
            # cannot really distinguish the registry hostname from image name on docker hub
            ((?P<registry>[^/]+\.[^/]+)/)?

            # Repository (required) - final component before any tag
            (?P<repository>[^:]+)

            # Tag (optional) - everything after the colon before @
            (?::(?P<tag>[^@]+))?

            # Digest (optional) - everything after @
            (?:@(?P<digest>.+))?
        """
        match = re.match(pattern, data, re.VERBOSE)
        if not match:
            raise ValueError(f"Invalid Docker image: {data}")

        image_id = handler(data)
        for name, value in match.groupdict().items():
            setattr(image_id, f"_{name}", value)

        # we need to construct a new object, because this is a frozen instance
        return image_id.model_copy(update={"root": str(image_id)})

    def __str__(self):
        digest = f"@{self.digest}" if self.digest else ""
        return f"{self.base}:{self.tag}{digest}"

    async def get_registry_auth_info(self) -> RegistryAuthInfo | None:
        if self.registry not in AUTH_URL_PER_REGISTRY:
            async with httpx.AsyncClient() as client:
                registry_resp = await client.get(self.get_manifest_url, follow_redirects=True)
                header = registry_resp.headers.get("www-authenticate")
            if not header:
                return None
            if not (match := re.match(r"(\w+)\s*(.*)", header)):
                raise ValueError(f"Invalid www authenticate header: {header}")
            auth_scheme, params_str = match.groups()

            if auth_scheme.lower() == "basic":
                AUTH_URL_PER_REGISTRY[self.registry] = RegistryAuthInfo(RegistryAuthScheme.BASIC, None)
            else:
                params = {}
                for param in re.finditer(r'(\w+)="([^"]*)"', params_str):
                    key, value = param.groups()
                    params[key] = value
                auth_url = (
                    f"{params['realm']}?service={params['service']}&scope=repository:{{repository}}:{{permissions}}"
                )
                AUTH_URL_PER_REGISTRY[self.registry] = RegistryAuthInfo(RegistryAuthScheme.BEARER, auth_url)

        return AUTH_URL_PER_REGISTRY[self.registry]

    def _basic_auth_header(self) -> dict[str, str]:
        if basic_auth := self.registry_config.basic_auth_str:
            return {"Authorization": f"Basic {basic_auth}"}
        return {}

    async def get_manifest(self) -> ManifestResponse:
        headers = base_headers.copy()

        if auth_header := await get_registry_auth_header(docker_image_id=self, permissions=(RegistryPermissions.PULL,)):
            headers["Authorization"] = auth_header

        async with httpx.AsyncClient() as client:
            manifest_resp = await client.get(self.get_manifest_url, headers=headers, follow_redirects=True)

            if manifest_resp.status_code != 200:
                raise Exception(f"Failed to get manifest: {manifest_resp.status_code}, {manifest_resp.text}")

            manifest_json = manifest_resp.json()
            digest = manifest_resp.headers.get("Docker-Content-Digest")
            if not digest:
                # Some registries (e.g. ECR) don't return Docker-Content-Digest header,
                # fall back to computing it from the response body
                digest = "sha256:" + hashlib.sha256(manifest_resp.content).hexdigest()

            return ManifestResponse(
                manifest=manifest_json,
                digest=digest,
            )

    async def resolve_version(self) -> ResolvedDockerImageID:
        manifest = await self.get_manifest()
        digest = manifest.digest
        result = ResolvedDockerImageID(
            registry=self.registry,
            repository=self.repository,
            tag=self.tag,
            digest=digest,
        )
        result._manifest = manifest.manifest
        return result


class ResolvedDockerImageID(BaseModel):
    registry: str
    repository: str
    tag: str
    digest: str
    _manifest: dict[str, Any] | None = PrivateAttr(None)

    @computed_field
    @cached_property
    def image_id(self) -> DockerImageID:
        return DockerImageID(root=f"{self.registry}/{self.repository}:{self.tag}@{self.digest}")

    async def get_manifest(self):
        if not self._manifest:
            self._manifest, _ = await self.image_id.get_manifest()
        return self._manifest

    async def get_labels(self) -> dict[str, str]:
        manifest = await self.get_manifest()

        headers = base_headers.copy()
        if auth_header := await get_registry_auth_header(docker_image_id=self.image_id):
            headers["Authorization"] = auth_header

        async with httpx.AsyncClient() as client:
            if "manifests" in manifest:
                manifest_resp = await client.get(
                    f"{self.image_id.manifest_base_url}/{manifest['manifests'][0]['digest']}",
                    headers=headers,
                    follow_redirects=True,
                )
                manifest = manifest_resp.raise_for_status().json()

            config_digest = manifest["config"]["digest"]
            config_url = f"{self.image_id.registry_base_url}/v2/{self.repository}/blobs/{config_digest}"
            config_resp = await client.get(config_url, headers=headers, follow_redirects=True)

            if config_resp.status_code != 200:
                raise Exception(f"Failed to get config: {config_resp.status_code}, {config_resp.text}")

            config = config_resp.json()
            return config.get("config", {}).get("Labels", {})

    def __str__(self) -> str:
        return str(self.image_id)


@alru_cache(ttl=timedelta(minutes=5).total_seconds())
async def get_registry_auth_header(
    *,
    docker_image_id: DockerImageID,
    permissions: tuple[RegistryPermissions] = (RegistryPermissions.PULL,),
) -> str | None:
    """Get the Authorization header value for a registry request.

    Returns a "Bearer <token>" or "Basic <credentials>" string, or None if no auth is needed.
    """
    try:
        auth_info = await docker_image_id.get_registry_auth_info()
    except Exception as ex:
        raise Exception(
            f"Image registry does not exist or is not accessible: {docker_image_id.get_manifest_url}"
        ) from ex

    if not auth_info:
        return None

    # Registries like ECR use Basic auth directly — no token exchange needed
    if auth_info.scheme == RegistryAuthScheme.BASIC:
        return docker_image_id._basic_auth_header().get("Authorization")

    # Bearer token flow (Docker Hub, GHCR, etc.)
    if auth_info.token_url:
        token_url = auth_info.token_url.format(
            repository=docker_image_id.repository, permissions=",".join(str(p) for p in permissions)
        )
        async with httpx.AsyncClient() as client:
            auth_resp = await client.get(
                token_url,
                follow_redirects=True,
                headers=docker_image_id._basic_auth_header(),
            )
            if auth_resp.status_code != 200:
                raise Exception(f"Failed to authenticate: {auth_resp.status_code}, {auth_resp.text}")
            return f"Bearer {auth_resp.json()['token']}"
    return None
