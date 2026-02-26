# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re

from pydantic import HttpUrl


def bridge_localhost_to_k8s(url: HttpUrl | str) -> HttpUrl:
    return HttpUrl(
        re.sub(
            r"localhost|127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}|0\.0\.0\.0",
            "host.docker.internal",
            str(url),
        )
    )


def bridge_k8s_to_localhost(url: HttpUrl | str) -> HttpUrl:
    return HttpUrl(re.sub(r"host.docker.internal", "localhost", str(url)))
