# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel


class CreateDiscoveryRequest(BaseModel):
    docker_image: str
