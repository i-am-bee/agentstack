# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""Minimal stub retained for historical migration compatibility.

The full Docker registry client was removed as part of the kagenti integration
(providers are now network-based, not Docker-image-based).  Only ``DockerImageID``
is kept because migration ``d39dd1ff796f`` imports it to recompute provider IDs.
"""

from __future__ import annotations

import re

from pydantic import RootModel, model_validator

_DOCKER_IMAGE_PATTERN = re.compile(
    r"^(?:(?P<registry>[^/]+\.[^/]+)/)?(?P<repository>[^:@]+)(?::(?P<tag>[^@]+))?(?:@(?P<digest>.+))?$"
)


class DockerImageID(RootModel):
    """Parses a Docker image reference into registry, repository, tag and digest."""

    root: str

    @model_validator(mode="after")
    def _parse(self) -> "DockerImageID":
        m = _DOCKER_IMAGE_PATTERN.match(self.root)
        if not m:
            raise ValueError(f"Invalid docker image reference: {self.root}")
        self._registry = m.group("registry") or "docker.io"
        self._repository = m.group("repository")
        self._tag = m.group("tag") or "latest"
        self._digest = m.group("digest")
        return self

    @property
    def base(self) -> str:
        return f"{self._registry}/{self._repository}"
