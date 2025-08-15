# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml

if typing.TYPE_CHECKING:
    from beeai_cli.commands.platform.base_driver import BaseDriver


async def install_security(driver: "BaseDriver"):
    """
    Setup istio and install gateway with TLS enabled.
    """

    await driver.run_in_vm(
        [
            "helm",
            "repo",
            "add",
            "istio",
            "https://istio-release.storage.googleapis.com/charts",
        ],
        "Adding istio charts to helm repo",
    )
    await driver.run_in_vm(
        [
            "helm",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "repo",
            "update",
        ],
        "Running helm repo update",
    )

    await driver.run_in_vm(
        [
            "helm",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "install",
            "istio-base",
            "istio/base",
            "-n",
            "istio-system",
            "--create-namespace",
            "--wait",
        ],
        "Installing istio-base",
    )

    await driver.run_in_vm(
        ["/bin/bash", "-c", "k3s kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null"],
        "Downloading gateway CRDS",
    )

    await driver.run_in_vm(
        [
            "/bin/bash",
            "-c",
            "k3s kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null",
        ],
        "installing gateway CRDS",
    )

    await driver.run_in_vm(
        [
            "helm",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "install",
            "istiod",
            "istio/istiod",
            "-n",
            "istio-system",
            "--set",
            "profile=ambient",
            "--set",
            "values.global.platform=k3s",
            "--wait",
        ],
        "Installing istiod",
    )

    await driver.run_in_vm(
        [
            "helm",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "install",
            "istio-cni",
            "istio/cni",
            "-n",
            "istio-system",
            "--set",
            "profile=ambient",
            "--set",
            "values.global.platform=k3s",
            "--wait",
        ],
        "Installing istio-cni",
    )

    await driver.run_in_vm(
        [
            "helm",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "install",
            "ztunnel",
            "istio/ztunnel",
            "-n",
            "istio-system",
            "--set",
            "profile=ambient",
            "--set",
            "values.global.platform=k3s",
            "--wait",
        ],
        "Installing istio-ztunnel",
    )

    await driver.run_in_vm(
        [
            "/bin/sh",
            "-c",
            "curl -LO https://cert-manager.io/public-keys/cert-manager-keyring-2021-09-20-1020CF3C033D4F35BAE1C19E1226061C665DF13E.gpg",
        ],
        "Downloading cert-manager gpg keyring",
    )

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
            "--verify",
            "--keyring",
            "./cert-manager-keyring-2021-09-20-1020CF3C033D4F35BAE1C19E1226061C665DF13E.gpg",
            "--set",
            "crds.enabled=true",
            "--wait",
        ],
        "Installing certificate manager...(used to auto-generate cert for gateway ingress)",
    )

    await driver.run_in_vm(
        [
            "/bin/sh",
            "-c",
            "k3s kubectl label namespace default istio.io/dataplane-mode=ambient",
        ],
        "Labeling the default namespace",
    )

    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "apply",
            "--server-side",
            "-f",
            "-",
        ],
        "Applying certificate issuer",
        input=yaml.dump(
            {
                "apiVersion": "cert-manager.io/v1",
                "kind": "Issuer",
                "metadata": {
                    "labels": {
                        "app.kubernetes.io/instance": "default-issuer",
                        "app.kubernetes.io/managed-by": "cert-manager-controller",
                        "app.kubernetes.io/name": "Issuer",
                    },
                    "name": "default-issuer",
                    "namespace": "default",
                },
                "spec": {"selfSigned": {}},
            }
        ).encode("utf-8"),
    )

    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "apply",
            "--server-side",
            "-f",
            "-",
        ],
        "Applying certificate issuer",
        input=yaml.dump(
            {
                "apiVersion": "cert-manager.io/v1",
                "kind": "Issuer",
                "metadata": {
                    "labels": {
                        "app.kubernetes.io/instance": "istio-system-issuer",
                        "app.kubernetes.io/managed-by": "cert-manager-controller",
                        "app.kubernetes.io/name": "Issuer",
                    },
                    "name": "istio-system-issuer",
                    "namespace": "istio-system",
                },
                "spec": {"selfSigned": {}},
            }
        ).encode("utf-8"),
    )

    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "apply",
            "--server-side",
            "-f",
            "-",
        ],
        "Applying gateway tls certificate",
        input=yaml.dump(
            {
                "apiVersion": "cert-manager.io/v1",
                "kind": "Certificate",
                "metadata": {
                    "name": "beeai-platform-tls",
                    "namespace": "istio-system",
                },
                "spec": {
                    "commonName": "beeai",
                    "dnsNames": [
                        "beeai",
                        "beeai.localhost",
                    ],
                    "issuerRef": {
                        "kind": "Issuer",
                        "name": "istio-system-issuer",
                    },
                    "secretName": "beeai-platform-tls",
                },
            }
        ).encode("utf-8"),
    )

    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "apply",
            "--server-side",
            "-f",
            "-",
        ],
        "Applying ingestion-svc tls certificate",
        input=yaml.dump(
            {
                "apiVersion": "cert-manager.io/v1",
                "kind": "Certificate",
                "metadata": {
                    "name": "ingestion-svc",
                    "namespace": "default",
                },
                "spec": {
                    "commonName": "ingestion-svc",
                    "dnsNames": [
                        "ingestion-svc",
                        "ingestion-svc.default",
                        "ingestion-svc.default.svc",
                        "ingestion-svc.default.svc.cluster.local",
                    ],
                    "issuerRef": {
                        "kind": "Issuer",
                        "name": "default-issuer",
                    },
                    "secretName": "ingestion-svc-tls",
                },
            }
        ).encode("utf-8"),
    )

    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "apply",
            "--server-side",
            "-f",
            "-",
        ],
        "Applying gateway CRD",
        input=yaml.dump(
            {
                "apiVersion": "gateway.networking.k8s.io/v1",
                "kind": "Gateway",
                "metadata": {
                    "name": "beeai-gateway",
                    "namespace": "istio-system",
                },
                "spec": {
                    "gatewayClassName": "istio",
                    "listeners": [
                        {
                            "name": "https",
                            "hostname": "beeai.localhost",
                            "port": 8336,
                            "protocol": "HTTPS",
                            "tls": {"mode": "Terminate", "certificateRefs": [{"name": "beeai-platform-tls"}]},
                            "allowedRoutes": {"namespaces": {"from": "Selector"}},
                        }
                    ],
                },
            }
        ).encode("utf-8"),
    )
    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "apply",
            "--server-side",
            "-f",
            "-",
        ],
        "Applying HTTPRoute CRD",
        input=yaml.dump(
            {
                "apiVersion": "gateway.networking.k8s.io/v1",
                "kind": "HTTPRoute",
                "metadata": {"name": "beeai-platform-api"},
                "spec": {
                    "parentRefs": [{"name": "beeai-gateway", "namespace": "istio-system"}],
                    "hostnames": ["beeai.localhost"],
                    "rules": [
                        {
                            "matches": [{"path": {"type": "PathPrefix", "value": "/api/v1"}}],
                            "backendRefs": [{"name": "beeai-platform-svc", "port": 8333}],
                        }
                    ],
                },
            }
        ).encode("utf-8"),
    )

    await driver.run_in_vm(
        [
            "k3s",
            "kubectl",
            "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "apply",
            "--server-side",
            "-f",
            "-",
        ],
        "Applying HTTPRoute CRD",
        input=yaml.dump(
            {
                "apiVersion": "gateway.networking.k8s.io/v1",
                "kind": "HTTPRoute",
                "metadata": {"name": "beeai-platform-ui"},
                "spec": {
                    "parentRefs": [{"name": "beeai-gateway", "namespace": "istio-system"}],
                    "hostnames": ["beeai-platform.testing", "beeai.localhost"],
                    "rules": [
                        {
                            "matches": [{"path": {"type": "PathPrefix", "value": "/"}}],
                            "backendRefs": [{"name": "beeai-platform-ui-svc", "port": 8334}],
                        }
                    ],
                },
            }
        ).encode("utf-8"),
    )

    await driver.run_in_vm(
        [
            "/bin/sh",
            "-c",
            "curl -L https://istio.io/downloadIstio | sh -",
        ],
        "Installing istioctl",
    )

    istio_dir = (
        (
            await driver.run_in_vm(
                [
                    "/bin/sh",
                    "-c",
                    "ls -lahF | grep istio | awk '{print $9}'",
                ],
                "Checking for istio install folder",
            )
        )
        .stdout.decode()
        .strip()
    )

    await driver.run_in_vm(
        [
            "/bin/sh",
            "-c",
            f"export PATH=/{istio_dir}/bin:$PATH && k3s kubectl apply -f /{istio_dir}samples/addons/prometheus.yaml",
        ],
        "Installing Prometheus",
    )

    await driver.run_in_vm(
        [
            "/bin/sh",
            "-c",
            f"export PATH=/{istio_dir}/bin:$PATH && k3s kubectl apply -f /{istio_dir}samples/addons/kiali.yaml",
        ],
        "Installing Kiali",
    )

    await driver.run_in_vm(
        [
            "/bin/sh",
            "-c",
            "k3s kubectl -n istio-system expose deployment kiali --protocol=TCP --port=20001 --target-port=20001 --type=NodePort --name=kiali-external",
        ],
        "Exposing Kiali service",
    )
