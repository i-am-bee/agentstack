# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import sys
import json
import requests
from pydantic import ValidationError

try:
    from a2a.types import AgentCard
except ImportError:
    print("Error: a2a-sdk is not installed. Please try installing it: pip install a2a-sdk pydantic")
    sys.exit(1)

def validate_agent_card(server_port):
    """Basic validation of an agent card"""
    if server_port.startswith("http://") or server_port.startswith("https://"):
        address = server_port
    else:
        address = f"http://{server_port}"
        
    if not address.endswith("/"):
        address += "/"

    target = f"{address}.well-known/agent-card.json"
    
    try:
        requests.get(address, timeout=5)
    except requests.exceptions.RequestException:
        return False, f"Could not connect to agent server at {address}. Is it running?"

    try:
        response = requests.get(target, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return False, f"Failed to fetch agent card: {e}"
    except json.JSONDecodeError as e:
        return False, f"Response is not valid JSON: {e}"
    
    try:
        card = AgentCard.model_validate(data)
    except ValidationError as e:
        return False, f"AgentCard schema validation failed:\n{e}"

    capabilities = card.capabilities
    extensions = capabilities.extensions or []
    extension_uris = [ext.uri for ext in extensions]

    has_trajectory = any("trajectory" in uri.lower() for uri in extension_uris)
    if not has_trajectory:
        return False, "Required [Trajectory] extension is missing! Every agent must include the Trajectory extension."

    return True, "Agent card is valid!"

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python validate-agent-card.py [server:port]")
        sys.exit(1)
    
    server_port = sys.argv[1] if len(sys.argv) == 2 else "127.0.0.1:8000"
    valid, message = validate_agent_card(server_port)
    print(message)
    sys.exit(0 if valid else 1)
