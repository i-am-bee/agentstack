# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml

if typing.TYPE_CHECKING:
    from agentstack_cli.commands.platform.base_driver import BaseDriver


async def install(driver: "BaseDriver"):
    # Gateway API
    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "apply",
            "-f",
            "https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml",
        ],
        "Installing gateway CRDs",
    )

    # Cert Manager
    await driver.run_in_vm(
        [
            "helm",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "install",
            "cert-manager",
            "oci://quay.io/jetstack/charts/cert-manager",
            "--version",
            "v1.18.2",
            "--namespace",
            "cert-manager",
            "--create-namespace",
            "--set",
            "crds.enabled=true",
            "--wait",
        ],
        "Installing cert-manager",
    )

    # Istio
    await driver.run_in_vm(
        ["helm", "repo", "add", "istio", "https://istio-release.storage.googleapis.com/charts"],
        "Adding Istio repo to Helm",
    )
    await driver.run_in_vm(["helm", "repo", "update"], "Updating Helm repos")
    for component in ["base", "istiod", "cni", "ztunnel"]:
        await driver.run_in_vm(
            [
                "helm",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
                "install",
                f"istio-{component}",
                f"istio/{component}",
                "--namespace",
                "istio-system",
                "--create-namespace",
                "--set=profile=ambient",
                "--set=global.platform=k3s",
                "--wait",
            ],
            f"Installing Istio ({component})",
        )
    await driver.run_in_vm(
        ["k3s", "kubectl", "label", "namespace", "default", "istio.io/dataplane-mode=ambient"],
        "Labeling the default namespace",
    )

    # Configuration
    Resource = typing.TypedDict(
        "Resource", {"apiVersion": str, "kind": str, "metadata": dict[str, str], "spec": dict[str, typing.Any]}
    )
    resources: list[Resource] = [
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Issuer",
            "metadata": {"name": "default-issuer", "namespace": "default"},
            "spec": {"selfSigned": {}},
        },
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Issuer",
            "metadata": {"name": "istio-system-issuer", "namespace": "istio-system"},
            "spec": {"selfSigned": {}},
        },
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Certificate",
            "metadata": {"name": "agentstack-tls", "namespace": "istio-system"},
            "spec": {
                "secretName": "agentstack-tls",
                "commonName": "agentstack",
                "dnsNames": ["agentstack", "agentstack.localhost"],
                "issuerRef": {"name": "istio-system-issuer", "kind": "Issuer"},
            },
        },
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Certificate",
            "metadata": {"name": "ingestion-svc", "namespace": "default"},
            "spec": {
                "secretName": "ingestion-svc-tls",
                "commonName": "ingestion-svc",
                "dnsNames": [
                    "ingestion-svc",
                    "ingestion-svc.default",
                    "ingestion-svc.default.svc",
                    "ingestion-svc.default.svc.cluster.local",
                ],
                "issuerRef": {"name": "default-issuer", "kind": "Issuer"},
            },
        },
        {
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "Gateway",
            "metadata": {"name": "agentstack-gateway", "namespace": "istio-system"},
            "spec": {
                "gatewayClassName": "istio",
                "listeners": [
                    {
                        "name": "https",
                        "hostname": "agentstack.localhost",
                        "port": 8336,
                        "protocol": "HTTPS",
                        "tls": {"mode": "Terminate", "certificateRefs": [{"name": "agentstack-tls"}]},
                        "allowedRoutes": {"namespaces": {"from": "All"}},
                    }
                ],
            },
        },
        {
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "HTTPRoute",
            "metadata": {"name": "agentstack-ui"},
            "spec": {
                "parentRefs": [{"name": "agentstack-gateway", "namespace": "istio-system"}],
                "hostnames": ["agentstack.testing", "agentstack.localhost"],
                "rules": [
                    {
                        "matches": [{"path": {"type": "PathPrefix", "value": "/"}}],
                        "backendRefs": [{"name": "agentstack-ui-svc", "port": 8334}],
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

    # Extra services
    for addon in ["prometheus", "kiali"]:
        await driver.run_in_vm(
            [
                "k3s",
                "kubectl",
                "apply",
                "-f",
                f"https://raw.githubusercontent.com/istio/istio/master/samples/addons/{addon}.yaml",
            ],
            f"Installing {addon.capitalize()}",
        )
    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "-n",
            "istio-system",
            "expose",
            "deployment",
            "kiali",
            "--protocol=TCP",
            "--port=20001",
            "--target-port=20001",
            "--type=LoadBalancer",
            "--name=kiali-external",
        ],
        "Exposing Kiali service",
    )
