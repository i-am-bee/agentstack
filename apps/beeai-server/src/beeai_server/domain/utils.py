# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import re

from pydantic import HttpUrl


def bridge_localhost_to_k8s(url: HttpUrl | str) -> HttpUrl:
    return HttpUrl(re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", str(url)))


def bridge_k8s_to_localhost(url: HttpUrl | str) -> HttpUrl:
    return HttpUrl(re.sub(r"host.docker.internal", "localhost", str(url)))
