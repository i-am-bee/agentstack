# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from agentstack_sdk.a2a.extensions.base import BaseExtensionSpec


class ExtensionError(Exception):
    extension: BaseExtensionSpec

    def __init__(self, spec: BaseExtensionSpec, message: str):
        super().__init__(f"Exception in extension '{spec.URI}': \n{message}")
