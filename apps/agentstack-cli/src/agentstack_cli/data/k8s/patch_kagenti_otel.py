# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""Helm post-renderer: patch kagenti-deps for local dev.

1. Removes the postgres-otel StatefulSet and its Service/ConfigMap
   (x86-only Fedora image, SCC-incompatible on MicroShift ARM).
2. Patches the Phoenix StatefulSet to use SQLite instead of PostgreSQL,
   removing the need for an external database entirely.
3. Upgrades the Phoenix image from kagenti's outdated 8.x to 12.31.2
   (matching the agentstack main branch) for GraphQL API compatibility.
4. Patches the container registry Service to NodePort 30500 so CRI-O on
   the host can pull images via the localhost mirror in registries.conf.
5. Replaces the upstream Keycloak image with the agentstack-themed build
   so the login UI matches the agentstack branding.
6. Patches the otel-collector filter/phoenix from a blocklist (a2a.* only)
   to an allowlist (openinference instrumentation scopes only), matching
   the agentstack helm chart's collector config.
"""

import os
import re
import sys

content = sys.stdin.read()

# The openinference allowlist filter rule (single OTTL condition).
# Only keeps spans from openinference instrumentation packages:
#   Python:     openinference.instrumentation.*
#   JavaScript: @arizeai/openinference-instrumentation-*
#   CrewAI:     crewai.telemetry
OPENINFERENCE_FILTER_RULE = (
    "not("
    'IsMatch(instrumentation_scope.name, "^openinference\\\\.instrumentation\\\\..*")'
    " or "
    'IsMatch(instrumentation_scope.name, "^@arizeai/openinference-instrumentation-.*")'
    " or "
    'instrumentation_scope.name == "crewai.telemetry"'
    ")"
)

PHOENIX_SQLITE_ENV = """\
        - name: PHOENIX_SQL_DATABASE_URL
          value: "sqlite:////mnt/data/phoenix.db"
        - name: PHOENIX_WORKING_DIR
          value: /mnt/data
        - name: PHOENIX_PORT
          value: "6006"
        - name: PHOENIX_GRPC_PORT
          value: "4317"
        - name: PHOENIX_ENABLE_AUTH
          value: "false"
"""

PHOENIX_ENV_REMOVE_PREFIXES = (
    "- name: PHOENIX_POSTGRES_",
    "- name: PHOENIX_SQL_DATABASE_POOL",
    "- name: PHOENIX_WORKING_DIR",
    "- name: PHOENIX_PORT",
    "- name: PHOENIX_GRPC_PORT",
)

docs = content.split("\n---\n")
result = []

for doc in docs:
    # Strip the postgres-otel StatefulSet
    if "kind: StatefulSet" in doc and "name: postgres-otel" in doc:
        continue
    # Strip the postgres-otel Service
    if "kind: Service" in doc and "app: postgres-otel" in doc:
        continue
    # Strip the postgres-otel ConfigMap (init scripts)
    if "kind: ConfigMap" in doc and "name: postgres-otel-init-script" in doc:
        continue

    # Patch Phoenix StatefulSet: replace postgres env vars with SQLite config
    if "kind: StatefulSet" in doc and "name: phoenix\n" in doc:
        lines = doc.split("\n")
        filtered = []
        skip_value_block = False
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(prefix) for prefix in PHOENIX_ENV_REMOVE_PREFIXES):
                skip_value_block = True
                continue
            if skip_value_block:
                if (
                    stripped.startswith("value")
                    or stripped.startswith("secretKeyRef")
                    or stripped.startswith("name:")
                    or stripped.startswith("key:")
                ):
                    continue
                skip_value_block = False
            filtered.append(line)
        doc = "\n".join(filtered)
        doc = re.sub(r"(        env:\n)", r"\1" + PHOENIX_SQLITE_ENV, doc, count=1)
        # Upgrade Phoenix image to 12.31.2 (kagenti ships 8.32.1 which lacks
        # the getTraceByOtelId GraphQL query needed by the feedback service).
        doc = re.sub(
            r"image: arizephoenix/phoenix:version-[\d.]+",
            "image: arizephoenix/phoenix:version-12.31.2",
            doc,
        )

    # Patch Keycloak: replace upstream image with agentstack-themed build.
    # The target image is passed via AGENTSTACK_KEYCLOAK_IMAGE env var from run.sh.
    keycloak_image = os.environ.get("AGENTSTACK_KEYCLOAK_IMAGE")
    if keycloak_image and "namespace: keycloak" in doc and ("kind: StatefulSet" in doc or "kind: Job" in doc):
        doc = re.sub(
            r"image: [^\s]*keycloak[^\s]*",
            f"image: {keycloak_image}",
            doc,
        )

    # Patch container registry Service: ClusterIP → NodePort 30500
    # so CRI-O on the host can pull via the localhost:30500 mirror.
    if "kind: Service" in doc and "namespace: cr-system" in doc and "app: registry" in doc:
        doc = re.sub(
            r"(spec:\n)",
            r"\1  type: NodePort\n",
            doc,
            count=1,
        )
        doc = re.sub(
            r"(- port: 5000\n\s+targetPort: 5000)",
            r"\1\n    nodePort: 30500",
            doc,
            count=1,
        )

    # Patch otel-collector-config: replace filter/phoenix span rules with openinference allowlist.
    if "kind: ConfigMap" in doc and "name: otel-collector-config" in doc:
        doc = re.sub(
            r"(filter/phoenix:\s*\n\s+traces:\s*\n(\s+)span:\s*\n)(?:\s+(?:-\s+|#).*\n?)+",
            lambda m: m.group(1) + m.group(2) + "  - '" + OPENINFERENCE_FILTER_RULE + "'\n",
            doc,
        )

    result.append(doc)

sys.stdout.write("\n---\n".join(result))
