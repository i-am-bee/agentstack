# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml

if typing.TYPE_CHECKING:
    from beeai_cli.commands.platform.base_driver import BaseDriver


async def install(driver: "BaseDriver"):
    # Configuration
    Resource = typing.TypedDict(
        "Resource", {"apiVersion": str, "kind": str, "metadata": dict[str, str], "spec": dict[str, typing.Any]}
    )

    resources: list[Resource] = [
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "default-deny-all-ingress", "namespace": "default"},
            "spec": {"podSelector": {}, "ingress": []},
        },
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "default-deny-all-egress", "namespace": "default"},
            "spec": {"policyTypes": ["Egress"], "podSelector": {}, "egress": []},
        },
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "beeai-platform-allow-all", "namespace": "default"},
            "spec": {
                "podSelector": {"matchLabels": {"app.kubernetes.io/name": "beeai-platform"}},
                "egress": [{}],
                "ingress": [{}],
            },
        },
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "default-egress-dns-policy", "namespace": "default"},
            "spec": {
                "policyTypes": ["Egress"],
                "podSelector": {},
                "egress": [
                    {
                        "to": [
                            {
                                "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}},
                                "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                            },
                        ],
                        "ports": [
                            {"port": 53, "protocol": "UDP"},
                            {"port": 53, "protocol": "TCP"},
                        ],
                    }
                ],
            },
        },
    ]

    for resource in resources:
        await driver.run_in_vm(
            ["k3s", "kubectl", "apply", "-f", "-"],
            f"Applying {resource['metadata']['name']} ({resource['kind']})",
            input=yaml.dump(resource, sort_keys=False).encode("utf-8"),
        )
