# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Final

from agentstack_sdk.a2a.extensions.ui.error import ErrorExtensionParams, ErrorExtensionServer, ErrorExtensionSpec

_IMPLICIT_DEPENDENCY_PREFIX: Final = "___server_dep"

DEFAULT_ERROR_EXTENSION: Final = ErrorExtensionServer(ErrorExtensionSpec(ErrorExtensionParams()))

__all__ = []
