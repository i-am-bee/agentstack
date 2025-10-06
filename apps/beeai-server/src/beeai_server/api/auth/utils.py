# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from starlette.datastructures import URL


def create_resource_uri(url: URL) -> str:
    return f"{url.scheme}://{url.netloc}{url.path}".rstrip("/")
