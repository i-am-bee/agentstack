# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


import re


def parse_bearer_mcp_www_authenticate(header: str) -> dict[str, str]:
    """
    Parses a WWW-Authenticate header like:
    Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource", scope="files:read"

    Returns a dict with the scheme and all parameters.
    """
    # Normalize: remove extra spaces/tabs/newlines
    header = header.strip()

    # Match the scheme (Bearer) and the rest
    match = re.match(r"^(\w+)\s+(.*)$", header, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid WWW-Authenticate header")

    scheme = match.group(1).strip()
    params_part = match.group(2)

    if scheme.lower() != "bearer":
        raise ValueError("Not a bearer scheme")

    # Extract all key="value" pairs (values are quoted)
    params = {}
    for k, v in re.findall(r'(\w+(?:_\w+)?)="([^"]*)"', params_part):
        params[k] = v

    # Also catch any unquoted values that might slip through (rare)
    for k, v in re.findall(r"(\w+(?:_\w+)?)=([^,\s]+)", params_part):
        if k not in params:
            params[k] = v

    return params
