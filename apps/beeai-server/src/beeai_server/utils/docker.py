# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Any

import httpx
from kink import inject
from pydantic import ModelWrapValidatorHandler, RootModel, model_validator, PrivateAttr

from beeai_server.configuration import Configuration


class DockerImageID(RootModel):
    root: str

    _registry: str | None = PrivateAttr(None)
    _repository: str = PrivateAttr()
    _tag: str | None = PrivateAttr(None)

    @property
    def registry(self) -> str:
        return self._registry or "docker.io"

    @property
    def repository(self) -> str | None:
        if self.registry.endswith("docker.io") and "/" not in self._repository:
            return f"library/{self._repository}"
        return self._repository

    @property
    def tag(self) -> str | None:
        return self._tag or "latest"

    @model_validator(mode="wrap")
    @classmethod
    def _parse(cls, data: Any, handler: ModelWrapValidatorHandler):
        image_id: DockerImageID = handler(data)

        pattern = r"""
            # Forbid starting with http:// or https://
            ^(?!https?://)
            
            # Registry (optional) - ends with slash and contains at least one dot
            ((?P<registry>[^/]+\.[^/]+)/)?
            
            # Repository (required) - final component before any tag
            (?P<repository>[^:]+)
            
            # Tag (optional) - everything after the colon
            (?::(?P<tag>[^:]+))?
        """
        match = re.match(pattern, image_id.root, re.VERBOSE)
        if not match:
            raise ValueError(f"Invalid Docker image: {data}")
        for name, value in match.groupdict().items():
            setattr(image_id, f"_{name}", value)
        image_id.root = str(image_id)  # normalize url
        return image_id

    def __str__(self):
        return f"{self.registry}/{self.repository}:{self.tag}"


auth_url_per_registry = {
    "ghcr.io": "https://ghcr.io/token?service=ghcr.io&scope=repository:{repository}:pull",
    "icr.io": "https://icr.io/oauth/token?service=registry&scope=repository:{repository}:pull",
    "docker.io": "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repository}:pull",
    "registry-1.docker.io": "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repository}:pull",
}


async def get_auth_endpoint(protocol: str, registry: str):
    if registry not in auth_url_per_registry:
        async with httpx.AsyncClient() as client:
            registry_resp = await client.get(f"{protocol}://{registry}/v2/_catalog", follow_redirects=True)
            header = registry_resp.headers.get("www-authenticate")
        if not header:
            return
        if not (match := re.match(r"(\w+)\s+(.*)", header)):
            raise ValueError(f"Invalid www authenticate header: {header}")
        auth_scheme, params_str = match.groups()
        params = {}
        for param in re.finditer(r'(\w+)="([^"]*)"', params_str):
            key, value = param.groups()
            params[key] = value
        auth_url = f"{params['realm']}?service={params['service']}&scope=repository:{{repository}}:pull"
        auth_url_per_registry[registry] = auth_url

    return auth_url_per_registry[registry]


@inject
async def get_registry_image_config_and_labels(image_id: DockerImageID, configuration: Configuration):
    # Parse image name to determine registry and repository
    headers = {
        "Accept": (
            "application/vnd.oci.image.index.v1+json,"
            "application/vnd.oci.image.manifest.v1+json,"
            "application/vnd.docker.distribution.manifest.list.v2+json,"
            "application/vnd.docker.distribution.manifest.v2+json"
        )
    }

    config = configuration.oci_registry[image_id.registry]
    protocol = config.protocol
    registry = image_id.registry

    if registry.endswith("docker.io"):
        registry = "registry-1.docker.io"

    try:
        token_endpoint = await get_auth_endpoint(protocol, registry)
    except Exception as ex:
        raise Exception("Image registry does not exist or is not accessible") from ex

    async with httpx.AsyncClient() as client:
        if token_endpoint:
            token_endpoint = token_endpoint.format(repository=image_id.repository)
            auth_resp = await client.get(
                token_endpoint,
                follow_redirects=True,
                headers=config.basic_auth_str and {"Authorization": f"Basic {config.basic_auth_str}"},
            )
            if auth_resp.status_code != 200:
                raise Exception(f"Failed to authenticate: {auth_resp.status_code}, {auth_resp.text}")
            token = auth_resp.json()["token"]
            headers["Authorization"] = f"Bearer {token}"

        manifest_url = f"{protocol}://{registry}/v2/{image_id.repository}/manifests"
        manifest_resp = await client.get(f"{manifest_url}/{image_id.tag}", headers=headers, follow_redirects=True)

        if manifest_resp.status_code != 200:
            raise Exception(f"Failed to get manifest: {manifest_resp.status_code}, {manifest_resp.text}")

        manifest = manifest_resp.json()

        if "manifests" in manifest:
            manifest_resp = await client.get(
                f"{manifest_url}/{manifest['manifests'][0]['digest']}", headers=headers, follow_redirects=True
            )
            manifest = manifest_resp.json()

        config_digest = manifest["config"]["digest"]
        config_url = f"{protocol}://{registry}/v2/{image_id.repository}/blobs/{config_digest}"
        config_resp = await client.get(config_url, headers=headers, follow_redirects=True)

        if config_resp.status_code != 200:
            raise Exception(f"Failed to get config: {config_resp.status_code}, {config_resp.text}")

        config = config_resp.json()
        labels = config.get("config", {}).get("Labels", {})
        return config, labels
