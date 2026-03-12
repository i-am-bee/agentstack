# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import configparser
import datetime
import functools
import importlib.metadata
import importlib.resources
import json
import os
import pathlib
import platform as platform_module
import shlex
import shutil
import sys
import tempfile
import textwrap
import typing
import uuid
from enum import StrEnum
from subprocess import CompletedProcess
from typing import TypedDict

import anyio
import httpx
import pydantic
import typer
import yaml
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_delay,
    wait_fixed,
)

from agentstack_cli.async_typer import AsyncTyper
from agentstack_cli.configuration import Configuration
from agentstack_cli.console import console
from agentstack_cli.utils import get_local_github_token, merge, run_command, verbosity

app = AsyncTyper()
configuration = Configuration()


@functools.cache
def detect_driver() -> typing.Literal["lima", "wsl"]:
    has_lima = (importlib.resources.files("agentstack_cli") / "data" / "bin" / "limactl").is_file() or shutil.which("limactl")
    arch = "aarch64" if platform_module.machine().lower() == "arm64" else platform_module.machine().lower()

    if platform_module.system() == "Windows" or shutil.which("wsl.exe"):
        return "wsl"
    elif has_lima and (
        os.path.exists("/System/Library/Frameworks/Virtualization.framework") or shutil.which(f"qemu-system-{arch}")
    ):
        return "lima"
    else:
        console.error("Could not find a compatible VM runtime.")
        if platform_module.system() == "Darwin":
            console.hint("This version of macOS is unsupported, please update the system.")
        elif platform_module.system() == "Linux":
            if not has_lima:
                console.hint(
                    "This Linux distribution is not suppored by Lima VM binary releases (required: glibc>=2.34). Manually install Lima VM by either:\n"
                    + "  - Your distribution's package manager, if available (https://repology.org/project/lima/versions)\n"
                    + "  - Homebrew for Linux, which uses its own separate glibc (https://brew.sh)\n"
                    + "  - Building it yourself, and ensuring that [green]limactl[/green] is in PATH (https://lima-vm.io/docs/installation/source/)"
                )
            if not shutil.which(f"qemu-system-{arch}"):
                console.hint(
                    f"QEMU is needed on Linux, please install it and ensure that [green]qemu-system-{arch}[/green] is in PATH. Refer to https://www.qemu.org/download/ for instructions."
                )
                console.hint(
                    f"On some distributions (e.g. RHEL) you might need to manually create the symlink: [green]sudo ln -s /usr/libexec/qemu-kvm /usr/bin/qemu-system-{arch}[/green]"
                )
        sys.exit(1)


@functools.cache
def detect_export_import_paths() -> tuple[str, str]:
    if detect_driver() == "lima":
        image_dir = pathlib.Path("/tmp/agentstack")
        image_dir.mkdir(exist_ok=True, parents=True)
        path = str(image_dir / f"{uuid.uuid4()}.tar")
        return (path, path)
    fd, tmp_path = tempfile.mkstemp(suffix=".tar")
    os.close(fd)
    windows_path = str(pathlib.Path(tmp_path).resolve().absolute())
    return (windows_path, f"/mnt/{windows_path[0].lower()}/{windows_path[2:].replace('\\', '/').removeprefix('/')}")


@functools.cache
def detect_limactl() -> str:
    bundled = importlib.resources.files("agentstack_cli") / "data" / "bin" / "limactl"
    return str(bundled) if bundled.is_file() else str(shutil.which("limactl"))


class LimaVMStatus(TypedDict):
    name: str
    status: str


async def detect_vm_status(vm_name: str) -> typing.Literal["running", "stopped", "missing"]:
    if detect_driver() == "lima":
        result = await run_command(
            [detect_limactl(), "--tty=false", "list", "--format=json"],
            "Looking for existing Agent Stack platform",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
        for line in result.stdout.decode().split("\n"):
            if line and (status_data := pydantic.TypeAdapter(LimaVMStatus).validate_json(line)).get("name") == vm_name:
                return "running" if status_data["status"].lower() == "running" else "stopped"
    else:
        for status, cmd in [("running", ["--running"]), ("stopped", [])]:
            if (
                vm_name
                in (
                    await run_command(
                        ["wsl.exe", "--list", "--quiet", *cmd],
                        f"Looking for {status} Agent Stack platform",
                        env={"WSL_UTF8": "1", "WSLENV": os.getenv("WSLENV", "") + ":WSL_UTF8"},
                    )
                )
                .stdout.decode()
                .splitlines()
            ):
                return "running" if status == "running" else "stopped"
    return "missing"


async def run_in_vm(
    vm_name: str,
    command: list[str],
    message: str,
    env: dict[str, str] | None = None,
    input: bytes | None = None,
    check: bool = True,
) -> CompletedProcess[bytes]:
    if detect_driver() == "lima":
        return await run_command(
            [detect_limactl(), "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--", "sudo", *command],
            message,
            env={"LIMA_HOME": str(Configuration().lima_home)} | (env or {}),
            cwd="/",
            input=input,
            check=check,
        )
    return await run_command(
        ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", *command],
        message,
        env={**(env or {}), "WSL_UTF8": "1", "WSLENV": "".join("{k}/u" for k in (env or {}).keys() | {"WSL_UTF8"})},
        input=input,
        check=check,
    )


#     ######  ########    ###    ########  ########
#    ##    ##    ##      ## ##   ##     ##    ##
#    ##          ##     ##   ##  ##     ##    ##
#     ######     ##    ##     ## ########     ##
#          ##    ##    ######### ##   ##      ##
#    ##    ##    ##    ##     ## ##    ##     ##
#     ######     ##    ##     ## ##     ##    ##


def canonify_image_tag(t: str) -> str:
    t = t.strip().strip("'").strip('"').replace(" @", "@")
    if "@" in t:
        base, digest = t.split("@")
        last_colon_idx = base.rfind(":")
        last_slash_idx = base.rfind("/")
        if last_colon_idx > last_slash_idx:
            base = base[:last_colon_idx]
        t = f"{base}@{digest}"
    return t if "." in t.split("/")[0] else f"docker.io/{t}"


async def detect_image_shas(
    vm_name: str,
    platform: str,
    loaded_images: set[str],
    *,
    mode: typing.Literal["guest", "host"],
) -> dict[str, str]:
    return {
        canon_tag: sha
        for line in (
            (
                await run_command(["docker", "images", "--digests"], "Listing host images")
                if mode == "host"
                else await run_in_vm(
                    vm_name,
                    {
                        "k3s": ["k3s", "ctr", "image", "ls"],
                        "microshift": ["crictl", "--timeout=30s", "images"],
                    }[platform],
                    "Listing guest images",
                )
            )
            .stdout.decode()
            .splitlines()[1:]
        )
        if (x := line.split())
        and len(x) >= 3
        and (x[1] != "<none>")
        and (canon_tag := canonify_image_tag(x[0] if mode == "guest" and platform == "k3s" else f"{x[0]}:{x[1]}"))
        in loaded_images
        and (sha := x[2])
    }


class ImagePullMode(StrEnum):
    guest = "guest"
    host = "host"
    hybrid = "hybrid"
    skip = "skip"


CHART_PREFIXES = ("kagenti-deps:", "kagenti:", "agentstack:")


def parse_scoped_set_values(set_values_list: list[str]) -> dict[str, list[str]]:
    """Split --set values by chart prefix. Unprefixed defaults to 'agentstack'."""
    result: dict[str, list[str]] = {"agentstack": [], "kagenti": [], "kagenti-deps": []}
    for value in set_values_list:
        for prefix in CHART_PREFIXES:
            if value.startswith(prefix):
                result[prefix.rstrip(":")].append(value[len(prefix) :])
                break
        else:
            result["agentstack"].append(value)
    return result


@app.command("start", help="Start Agent Stack platform. [Local only]")
async def start_cmd(
    set_values_list: typing.Annotated[
        list[str],
        typer.Option(
            "--set",
            help="Set Helm chart values. Prefix with chart name: --set kagenti:key=val, --set kagenti-deps:key=val. Unprefixed applies to agentstack.",
            default_factory=list,
        ),
    ],
    image_pull_mode: typing.Annotated[
        ImagePullMode,
        typer.Option(
            "--image-pull-mode",
            help=textwrap.dedent(
                """\
                guest = pull all images inside VM [default]
                host = pull unavailable images on host, then import all
                hybrid = import available images from host, pull the rest in VM
                skip = skip explicit pull step (Kubernetes will attempt to pull missing images)
                """
            ),
        ),
    ] = ImagePullMode.guest,
    values_file: typing.Annotated[
        pathlib.Path | None,
        typer.Option(
            "-f",
            help="YAML values file with chart-scoped sections: agentstack:, kagenti:, kagenti-deps:",
        ),
    ] = None,
    lima_image: typing.Annotated[
        str | None, typer.Option("--lima-image", help="Local path or URL to Lima image (.qcow2)")
    ] = None,
    wsl_image: typing.Annotated[
        str | None, typer.Option("--wsl-image", help="Local path or URL to WSL distro image (.wsl)")
    ] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
    skip_login: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    no_wait_for_platform: typing.Annotated[bool, typer.Option(hidden=True)] = False,
):
    import agentstack_cli.commands.server

    if values_file and not await anyio.Path(values_file).is_file():
        raise FileNotFoundError(f"Values file {values_file} not found.")

    # Parse chart-scoped values from -f file and --set flags
    user_values = yaml.safe_load(pathlib.Path(values_file).read_text()) if values_file else {}  # noqa: ASYNC240
    user_agentstack_values = user_values.get("agentstack", {}) if isinstance(user_values, dict) else {}
    user_kagenti_values = user_values.get("kagenti", {}) if isinstance(user_values, dict) else {}
    user_kagenti_deps_values = user_values.get("kagenti-deps", {}) if isinstance(user_values, dict) else {}
    scoped_sets = parse_scoped_set_values(set_values_list)

    with verbosity(verbose):
        version = importlib.metadata.version("agentstack-cli").replace("rc", "-rc")
        arch = "x86_64" if platform_module.machine().lower() in ["x86_64", "amd64"] else "aarch64"
        Configuration().home.mkdir(exist_ok=True)
        match detect_driver():
            case "lima":
                lima_env = {"LIMA_HOME": str(Configuration().lima_home)}
                match await detect_vm_status(vm_name):
                    case "missing":
                        for legacy in [vm_name, "beeai-platform"]:
                            await run_command(
                                [detect_limactl(), "--tty=false", "delete", "--force", legacy],
                                f"Cleaning up remains of {'previous' if legacy == vm_name else 'legacy'} instance",
                                env=lima_env,
                                check=False,
                                cwd="/",
                            )
                        import psutil

                        total_memory_gib = psutil.virtual_memory().total // (1024**3)
                        if total_memory_gib < 4:
                            console.error("Not enough memory. Agent Stack platform requires at least 4 GB of RAM.")
                            sys.exit(1)
                        if total_memory_gib < 8:
                            console.warning("Less than 8 GB of RAM detected. Performance may be degraded.")

                        current_lima_image = (
                            lima_image
                            or f"https://github.com/i-am-bee/agentstack/releases/download/v{version}/microshift-vm-{arch}.qcow2"
                        )


                        if current_lima_image.startswith("/") or current_lima_image.startswith("./"):
                            current_lima_image = str(await anyio.Path(current_lima_image).absolute())

                        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete_on_close=False) as f:
                            f.write(
                                yaml.dump(
                                    {
                                        "env": {"KUBECONFIG": "/kubeconfig"},
                                        "images": [
                                            {
                                                "location": current_lima_image,
                                                "arch": arch,
                                            },
                                        ],
                                        "portForwards": [
                                            {
                                                "guestIP": "127.0.0.1",
                                                "guestPortRange": [1024, 65535],
                                                "hostPortRange": [1024, 65535],
                                                "hostIP": "127.0.0.1",
                                            },
                                            {"guestIP": "0.0.0.0", "proto": "any", "ignore": True},
                                        ],
                                        "mounts": [
                                            {
                                                "location": "/tmp/agentstack",
                                                "mountPoint": "/tmp/agentstack",
                                                "writable": True,
                                            }
                                        ],
                                        "mountTypesUnsupported": ["9p"],
                                        "containerd": {"system": False, "user": False},
                                        "hostResolver": {"hosts": {"host.docker.internal": "host.lima.internal"}},
                                        "memory": f"{round(min(8.0, max(3.0, total_memory_gib / 2)))}GiB",
                                    }
                                )
                            )
                            f.flush()
                            f.close()
                            await run_command(
                                [detect_limactl(), "--tty=false", "start", f.name, f"--name={vm_name}"],
                                "Creating a Lima VM",
                                env=lima_env,
                                cwd="/",
                            )
                    case "stopped":
                        await run_command(
                            [detect_limactl(), "--tty=false", "start", vm_name], "Starting up", env=lima_env, cwd="/"
                        )
                    case "running":
                        console.info("Updating an existing instance.")
            case "wsl":
                if (await run_command(["wsl.exe", "--status"], "Checking for WSL2", check=False)).returncode != 0:
                    console.error(
                        "WSL is not installed. Please follow the Agent Stack installation instructions: https://agentstack.beeai.dev/stable/introduction/quickstart#windows"
                    )
                    console.hint(
                        "Run [green]wsl.exe --install[/green] as administrator. If you just did this, restart your PC and run the same command again. Full installation may require up to two restarts. WSL is properly set up once you reach a working Linux terminal. You can verify this by running [green]wsl.exe[/green] without arguments."
                    )
                    sys.exit(1)
                config_file_path = (
                    pathlib.Path.home()
                    if platform_module.system() == "Windows"
                    else pathlib.Path(
                        (
                            await run_command(
                                ["/bin/sh", "-c", '''wslpath "$(cmd.exe /c 'echo %USERPROFILE%')"'''],
                                "Detecting home path",
                            )
                        )
                        .stdout.decode()
                        .strip()
                    )
                ) / ".wslconfig"
                config_file_path.touch()
                with config_file_path.open("r+") as f:
                    content = f.read()
                    config = configparser.ConfigParser()
                    config.read_string(content)
                    if not config.has_section("wsl2"):
                        config.add_section("wsl2")
                    wsl2_networking_mode = config.get("wsl2", "networkingMode", fallback=None)
                    if wsl2_networking_mode and wsl2_networking_mode != "nat":
                        config.set("wsl2", "networkingMode", "nat")
                        f.seek(0)
                        f.truncate(0)
                        config.write(f)
                        if platform_module.system() == "Linux":
                            console.warning(
                                "WSL networking mode updated. Please close WSL, run [green]wsl --shutdown[/green] from PowerShell, re-open WSL and run [green]agentstack platform start[/green] again."
                            )
                            sys.exit(1)
                        await run_command(["wsl.exe", "--shutdown"], "Updating WSL2 networking")
                Configuration().home.mkdir(exist_ok=True)
                if await detect_vm_status(vm_name) == "missing":
                    await run_command(
                        ["wsl.exe", "--unregister", vm_name], "Cleaning up remains of previous instance", check=False
                    )
                    await run_command(
                        ["wsl.exe", "--unregister", "beeai-platform"],
                        "Cleaning up remains of legacy instance",
                        check=False,
                    )

                    current_wsl_image = (
                        wsl_image
                        or f"https://github.com/i-am-bee/agentstack/releases/download/v{version}/microshift-vm-{arch}.wsl"
                    )
                    install_dir = Configuration().home / "wsl" / vm_name
                    install_dir.mkdir(parents=True, exist_ok=True)
                    if current_wsl_image.startswith("http://") or current_wsl_image.startswith("https://"):
                        with tempfile.NamedTemporaryFile(suffix=".wsl", delete=True, delete_on_close=False) as tmp:
                            with console.status("Downloading WSL distribution...", spinner="dots"):
                                async with httpx.AsyncClient(follow_redirects=True) as client:
                                    async with client.stream("GET", current_wsl_image) as response:
                                        response.raise_for_status()
                                        async for chunk in response.aiter_bytes():
                                            tmp.write(chunk)
                            tmp.close()
                            await run_command(
                                ["wsl.exe", "--import", vm_name, str(install_dir), tmp.name],
                                "Importing WSL distribution",
                            )
                    else:
                        await run_command(
                            ["wsl.exe", "--import", vm_name, str(install_dir), current_wsl_image],
                            "Importing WSL distribution",
                        )
                    await run_command(["wsl.exe", "--terminate", vm_name], "Restarting Agent Stack VM")
                await run_in_vm(vm_name, ["/usr/bin/setsid", "-f", "/usr/bin/sleep", "infinity"], "Ensuring persistence of Agent Stack VM")
                await run_in_vm(
                    vm_name,
                    [
                        "bash",
                        "-c",
                        "echo $(ip route show | grep -i default | cut -d' ' -f3) host.docker.internal >> /etc/hosts",
                    ],
                    "Setting up internal networking",
                )

        detected_platform: typing.Literal["k3s", "microshift"] | None = None
        try:
            detected_platform = typing.cast(
                typing.Literal["k3s", "microshift"],
                (
                    (
                        await run_in_vm(
                            vm_name,
                            ["bash", "-c", "command -v k3s || command -v microshift"],
                            "Detecting Kubernetes platform",
                        )
                    )
                    .stdout.decode()
                    .strip()
                    .splitlines()[0]
                    .split("/")[-1]
                ),
            )
        except Exception:
            pass

        match detected_platform:
            case None:
                await run_in_vm(
                    vm_name,
                    [
                        "bash",
                        "-c",
                        textwrap.dedent("""\
                            sysctl -w net.ipv4.ip_forward=1
                            mkdir -p /tmp/microshift-install
                            curl -fsSL "https://github.com/microshift-io/microshift/releases/download/4.21.0_g29f429c21_4.21.0_okd_scos.ec.15/microshift-debs-$(uname -m).tgz" | tar -xz -C /tmp/microshift-install &
                            eatmydata apt-get update -y -q
                            eatmydata apt-get install -y -q --no-install-recommends skopeo cri-o cri-tools containernetworking-plugins kubectl
                            mkdir -p -m 777 /postgresql-data /seaweedfs-data /registry-data /redis-data
                            systemctl enable --now crio
                            wait
                            eatmydata dpkg -i /tmp/microshift-install/microshift_*.deb /tmp/microshift-install/microshift-kindnet_*.deb
                            rm -rf /tmp/microshift-install
                            systemctl enable --now microshift
                        """),
                    ],
                    "Installing MicroShift",
                )
            case "k3s":
                await run_in_vm(
                    vm_name,
                    [
                        "bash",
                        "-c",
                        "apt-get install -y -q skopeo; systemctl is-active --quiet k3s || systemctl enable --now k3s",
                    ],
                    "Refreshing existing k3s VM",
                )
            case "microshift":
                await run_in_vm(
                    vm_name,
                    [
                        "bash",
                        "-c",
                        "systemctl is-active --quiet crio && systemctl is-active --quiet microshift || systemctl enable --now crio && systemctl enable --now microshift",
                    ],
                    "Refreshing existing MicroShift VM",
                )

        platform: typing.Literal["k3s", "microshift"] = detected_platform or "microshift"
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                f"ln -sf {'/etc/rancher/k3s/k3s.yaml' if platform == 'k3s' else '/var/lib/microshift/resources/kubeadmin/kubeconfig'} /kubeconfig && chmod 644 /kubeconfig",
            ],
            "Setting up kubeconfig symlink",
        )
        kubeconfig_local = anyio.Path(Configuration().lima_home) / vm_name / "copied-from-guest" / "kubeconfig.yaml"
        await kubeconfig_local.parent.mkdir(parents=True, exist_ok=True)
        await kubeconfig_local.write_text(
            (
                await run_in_vm(
                    vm_name,
                    [
                        "timeout",
                        "5m",
                        "bash",
                        "-c",
                        'until grep -q "current-context:" /kubeconfig 2>/dev/null; do sleep 5; done && cat /kubeconfig',
                    ],
                    "Copying kubeconfig from Agent Stack platform",
                )
            ).stdout.decode()
        )
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                textwrap.dedent("""\
                    command -v helm && exit 0
                    case $(uname -m) in x86_64) ARCH="amd64" ;; aarch64) ARCH="arm64" ;; esac
                    curl -fsSL "https://get.helm.sh/helm-v4.1.1-linux-${ARCH}.tar.gz" | tar -xzf - --strip-components=1 -C /usr/local/bin "linux-${ARCH}/helm"
                    chmod +x /usr/local/bin/helm
                """),
            ],
            "Installing Helm",
        )
        # --- Prepare agentstack chart and import images before any deployments ---
        await run_in_vm(
            vm_name,
            ["bash", "-c", "cat >/tmp/agentstack-chart.tgz"],
            "Preparing Helm chart",
            input=(importlib.resources.files("agentstack_cli") / "data" / "helm-chart.tgz").read_bytes(),
        )
        await run_in_vm(
            vm_name,
            ["bash", "-c", "cat >/tmp/agentstack-values.yaml"],
            "Preparing Helm values",
            input=yaml.dump(
                merge(
                    {
                        "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",
                        "trustProxyHeaders": True,
                        "localStorage": platform == "microshift",  # k3s uses local path provisioner instead
                        "keycloak": {
                            "enabled": False,
                            "auth": {
                                "adminUser": "admin",
                                "adminPassword": "admin",
                                "seedAgentstackUsers": [
                                    {
                                        "username": "admin",
                                        "password": "admin",
                                        "firstName": "Admin",
                                        "lastName": "User",
                                        "email": "admin@beeai.dev",
                                        "roles": ["agentstack-admin", "kagenti-admin"],
                                        "enabled": True,
                                    }
                                ],
                            },
                        },
                        "externalOidcProvider": {
                            "issuerUrl": "http://keycloak-service.keycloak:8080/realms/agentstack",
                            "publicIssuerUrl": "http://keycloak.localtest.me:8080/realms/agentstack",
                            "name": "Keycloak",
                            "id": "keycloak",
                            "rolesPath": "realm_access.roles",
                            "uiClientId": "agentstack-ui",
                            "uiClientSecret": "agentstack-ui-secret",
                            "serverClientId": "agentstack-server",
                            "serverClientSecret": "agentstack-server-secret",
                        },
                        "auth": {
                            "enabled": True,
                            "provisionKeycloak": True,
                            "validateAudience": False,
                            "nextauthUrl": "http://agentstack.localtest.me:8080",
                            "apiUrl": "http://agentstack-api.localtest.me:8080",
                        },
                        "features": {"uiLocalSetup": True},
                        "providerBuilds": {"enabled": True},
                        "disableProviderDownscaling": True,
                        "cors": {
                            "enabled": True,
                            "allowOriginRegex": r"https?://(localhost|127\.0\.0\.1|[a-z0-9.-]*\.?localtest\.me)(:\d+)?",
                            "allowCredentials": True,
                        },
                    },
                    user_agentstack_values,
                )
            ).encode("utf-8"),
        )
        # --- Prepare kagenti chart values and version before image listing ---
        kagenti_chart_version = "0.5.1"
        kagenti_deps_values = yaml.dump(
            merge(
                {
                    "openshift": False,
                    "components": {
                        "keycloak": {"enabled": True},
                        "istio": {"enabled": False},
                        "kiali": {"enabled": False},
                        "mcpInspector": {"enabled": False},
                        "otel": {"enabled": False},
                        "mlflow": {"enabled": False},
                        "containerRegistry": {"enabled": True},
                        "spire": {"enabled": False},
                        "tekton": {"enabled": False},
                        "shipwright": {"enabled": False},
                        "certManager": {"enabled": False},
                        "gatewayApi": {"enabled": False},
                        "metricsServer": {"enabled": False},
                        "ingressGateway": {"enabled": True},
                    },
                    "keycloak": {
                        "namespace": "keycloak",
                        "auth": {"adminUser": "admin", "adminPassword": "admin"},
                        "url": "http://keycloak-service.keycloak:8080",
                        "publicUrl": "http://keycloak.localtest.me:8080",
                    },
                },
                user_kagenti_deps_values,
            )
        )
        kagenti_values = yaml.dump(
            merge(
                {
                    "openshift": False,
                    "components": {
                        "agentOperator": {"enabled": False},
                        "platformWebhook": {"enabled": False},
                        "agentNamespaces": {"enabled": True},
                        "ui": {"enabled": True},
                        "mcpGateway": {"enabled": False},
                        "istio": {"enabled": False},
                    },
                    "agentNamespaces": ["team1"],
                    "keycloak": {
                        "enabled": True,
                        "namespace": "keycloak",
                        "url": "http://keycloak-service.keycloak:8080",
                        "publicUrl": "http://keycloak.localtest.me:8080",
                        "realm": "agentstack",
                        "autoBootstrapRealm": False,
                        "adminSecretName": "keycloak-initial-admin",
                        "adminUsernameKey": "username",
                        "adminPasswordKey": "password",
                    },
                    "ui": {
                        "auth": {"enabled": True},
                        "namespace": "kagenti-system",
                        "domainName": "localtest.me",
                        "hostname": "kagenti-ui.localtest.me",
                        "url": "http://kagenti-ui.localtest.me:8080",
                        "api": {"hostname": "kagenti-api.localtest.me"},
                    },
                    "apiOAuthSecret": {"enabled": True},
                    "spire": {"enabled": False},
                },
                user_kagenti_values,
            )
        )
        await run_in_vm(
            vm_name,
            ["bash", "-c", "cat >/tmp/kagenti-deps-values.yaml"],
            "Preparing kagenti-deps values",
            input=kagenti_deps_values.encode("utf-8"),
        )
        await run_in_vm(
            vm_name,
            ["bash", "-c", "cat >/tmp/kagenti-values.yaml"],
            "Preparing kagenti values",
            input=kagenti_values.encode("utf-8"),
        )
        # List images from all charts (agentstack + kagenti + kagenti-deps)
        image_sed = r"sed -n '/^\s*image:/{ /{{/!{ s/.*image:\s*//p } }'"
        loaded_images = {
            canonify_image_tag(typing.cast(str, yaml.safe_load(line)))
            for line in (
                await run_in_vm(
                    vm_name,
                    [
                        "/bin/bash",
                        "-c",
                        "{ "
                        + "helm template agentstack /tmp/agentstack-chart.tgz --values=/tmp/agentstack-values.yaml "
                        + " ".join(shlex.quote(f"--set={v}") for v in scoped_sets["agentstack"])
                        + "; "
                        + f"helm template kagenti-deps oci://ghcr.io/kagenti/kagenti/kagenti-deps --version={kagenti_chart_version} --values=/tmp/kagenti-deps-values.yaml "
                        + " ".join(shlex.quote(f"--set={v}") for v in scoped_sets["kagenti-deps"])
                        + "; "
                        + f"helm template kagenti oci://ghcr.io/kagenti/kagenti/kagenti --version={kagenti_chart_version} --values=/tmp/kagenti-values.yaml "
                        + " ".join(shlex.quote(f"--set={v}") for v in scoped_sets["kagenti"])
                        + "; } | " + image_sed,
                    ],
                    "Listing necessary images",
                )
            )
            .stdout.decode()
            .splitlines()
        }
        # The post-renderer strips the x86-only Fedora postgres image and its reference
        # won't appear in helm template output, so no extra image additions needed.
        # Add the keycloak-themed image: the agentstack chart has keycloak disabled
        # (kagenti-deps deploys it), but we patch kagenti's keycloak to use our themed image.
        keycloak_image = (
            await run_in_vm(
                vm_name,
                [
                    "bash", "-c",
                    "helm template agentstack /tmp/agentstack-chart.tgz"
                    " --values=/tmp/agentstack-values.yaml"
                    " --set keycloak.enabled=true --set auth.enabled=true"
                    " --show-only templates/keycloak/statefulset.yaml "
                    + " ".join(shlex.quote(f"--set={v}") for v in scoped_sets.get("agentstack", []))
                    + " | grep -m1 'image:.*keycloak' | sed 's/.*image: *//;s/\"//g' | tr -d ' '",
                ],
                "Resolving keycloak image from agentstack chart",
            )
        ).stdout.decode().strip()
        if keycloak_image:
            loaded_images.add(keycloak_image)
        images_to_import_from_host, shas_guest_before = set[str](), {}
        if image_pull_mode in {ImagePullMode.host, ImagePullMode.hybrid}:
            if platform == "microshift":
                await run_in_vm(
                    vm_name,
                    ["timeout", "2m", "bash", "-c", "until crictl info >/dev/null 2>&1; do sleep 2; done"],
                    "Waiting for CRI-O to be ready",
                )
            shas_guest_before = await detect_image_shas(vm_name, platform, loaded_images, mode="guest")
            shas_host = await detect_image_shas(vm_name, platform, loaded_images, mode="host")
            if image_pull_mode == ImagePullMode.host:
                for image in loaded_images - shas_host.keys():
                    await run_command(["docker", "pull", image], f"Pulling image {image} on host")
                shas_host = await detect_image_shas(vm_name, platform, loaded_images, mode="host")
            images_to_import_from_host = dict(shas_host.items() - shas_guest_before.items()).keys() & loaded_images
            if images_to_import_from_host:
                host_path, guest_path = detect_export_import_paths()
                try:
                    await run_command(
                        ["docker", "image", "save", "-o", host_path, *images_to_import_from_host],
                        f"Exporting image{'' if len(images_to_import_from_host) == 1 else 's'} {', '.join(images_to_import_from_host)} from Docker",
                    )
                    await run_in_vm(
                        vm_name,
                        [
                            "bash",
                            "-c",
                            f"k3s ctr images import {guest_path}"
                            if platform == "k3s"
                            else "\n".join(
                                f"skopeo copy docker-archive:{guest_path}:{img} containers-storage:{img} &"
                                for img in images_to_import_from_host
                            )
                            + "\nwait",
                        ],
                        f"Importing image{'' if len(images_to_import_from_host) == 1 else 's'} {', '.join(images_to_import_from_host)} into Agent Stack platform",
                    )
                finally:
                    await anyio.Path(host_path).unlink(missing_ok=True)
        if image_pull_mode in {ImagePullMode.guest, ImagePullMode.hybrid}:
            github_token = get_local_github_token()
            for image in loaded_images - images_to_import_from_host:
                await run_in_vm(
                    vm_name,
                    ["k3s", "ctr", "image", "pull", image]
                    if platform == "k3s"
                    else [
                        "skopeo",
                        "copy",
                        *(["--src-username", "x-access-token", "--src-password", github_token] if github_token and image.startswith("ghcr.io/") else []),
                        f"docker://{image}",
                        f"containers-storage:{image}",
                    ],
                    f"Pulling image {image}",
                    env={"GITHUB_TOKEN": github_token} if github_token and image.startswith("ghcr.io/") else None,
                )

        # --- Kagenti platform installation ---
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                textwrap.dedent("""\
                    kubectl --kubeconfig=/kubeconfig apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/standard-install.yaml
                """),
            ],
            "Installing kagenti prerequisites (Gateway API CRDs)",
        )
        # Install Istio as Gateway API controller (same charts/version as kagenti ansible installer)
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                textwrap.dedent("""\
                    ISTIO_VERSION=1.28.0
                    ISTIO_REPO=https://istio-release.storage.googleapis.com/charts/
                    helm repo add istio "$ISTIO_REPO" 2>/dev/null || true
                    helm repo update istio
                    kubectl --kubeconfig=/kubeconfig create namespace istio-system --dry-run=client -o yaml | kubectl --kubeconfig=/kubeconfig apply -f -
                    helm upgrade --install istio-base istio/base --version=$ISTIO_VERSION --namespace=istio-system --kubeconfig=/kubeconfig --wait --force-conflicts
                    helm upgrade --install istiod istio/istiod --version=$ISTIO_VERSION --namespace=istio-system --kubeconfig=/kubeconfig --wait --force-conflicts \
                        --set pilot.resources.requests.cpu=50m \
                        --set pilot.resources.requests.memory=256Mi
                """),
            ],
            "Installing Istio (Gateway API controller)",
        )
        # Create hostPath PVs (MicroShift has no dynamic storage provisioner)
        k8s_data = importlib.resources.files("agentstack_cli") / "data" / "k8s"
        if platform == "microshift":
            keycloak_pv_yaml = (k8s_data / "keycloak-postgres-pv.yaml").read_text()
            await run_in_vm(
                vm_name,
                ["bash", "-c", "mkdir -p /kagenti-keycloak-postgres-data && chmod 777 /kagenti-keycloak-postgres-data && kubectl --kubeconfig=/kubeconfig apply -f -"],
                "Creating PV for kagenti Keycloak Postgres",
                input=keycloak_pv_yaml.encode("utf-8"),
            )
            if any("components.otel.enabled=true" in v.lower() for v in scoped_sets.get("kagenti-deps", [])):
                phoenix_pv_yaml = (k8s_data / "phoenix-data-pv.yaml").read_text()
                await run_in_vm(
                    vm_name,
                    ["bash", "-c", "mkdir -p /phoenix-data && chmod 777 /phoenix-data && kubectl --kubeconfig=/kubeconfig apply -f -"],
                    "Creating PV for Phoenix data",
                    input=phoenix_pv_yaml.encode("utf-8"),
                )
        # Install a Helm 4 post-renderer plugin that strips the postgres-otel
        # StatefulSet from kagenti-deps (x86-only Fedora image) and patches Phoenix
        # to use SQLite instead of PostgreSQL for local dev.
        otel_enabled = any("components.otel.enabled=true" in v.lower() for v in scoped_sets.get("kagenti-deps", []))
        kagenti_deps_post_renderer: list[str] = []
        if otel_enabled:
            patch_script = (importlib.resources.files("agentstack_cli") / "data" / "k8s" / "patch_kagenti_otel.py").read_text()
            await run_in_vm(
                vm_name,
                [
                    "bash", "-c",
                    textwrap.dedent("""\
                        PLUGIN_DIR=/tmp/helm-plugin-patch-postgres
                        mkdir -p "$PLUGIN_DIR"
                        cat > "$PLUGIN_DIR/plugin.yaml" << 'YAML'
                        apiVersion: v1
                        type: postrenderer/v1
                        name: patch-postgres
                        version: 0.1.0
                        runtime: subprocess
                        runtimeConfig:
                          platformCommand:
                            - command: ${HELM_PLUGIN_DIR}/run.sh
                        YAML
                        cat > "$PLUGIN_DIR/patch.py"
                    """),
                ],
                "Preparing post-renderer patch script",
                input=patch_script.encode("utf-8"),
            )
            # Write run.sh separately to avoid shebang escaping issues with bash -c
            await run_in_vm(
                vm_name,
                [
                    "python3", "-c",
                    "import os; "
                    "p='/tmp/helm-plugin-patch-postgres/run.sh'; "
                    f"open(p,'wb').write(b'\\x23\\x21/bin/bash\\nset -e\\nexport AGENTSTACK_KEYCLOAK_IMAGE={shlex.quote(keycloak_image)}\\nexec python3 /tmp/helm-plugin-patch-postgres/patch.py\\n'); "
                    "os.chmod(p, 0o755)",
                ],
                "Writing post-renderer entrypoint",
            )
            await run_in_vm(
                vm_name,
                ["helm", "plugin", "install", "/tmp/helm-plugin-patch-postgres"],
                "Installing post-renderer plugin",
                check=False,  # already installed on subsequent runs
            )
            kagenti_deps_post_renderer = ["--post-renderer=patch-postgres"]
        await run_in_vm(
            vm_name,
            [
                "helm",
                "upgrade",
                "--install",
                "kagenti-deps",
                "oci://ghcr.io/kagenti/kagenti/kagenti-deps",
                f"--version={kagenti_chart_version}",
                "--namespace=kagenti-system",
                "--create-namespace",
                "--values=/tmp/kagenti-deps-values.yaml",
                "--timeout=10m",
                "--kubeconfig=/kubeconfig",
                "--force-conflicts",
                *kagenti_deps_post_renderer,
                *(f"--set={v}" for v in scoped_sets["kagenti-deps"]),
            ],
            "Installing kagenti dependencies (Keycloak)",
        )
        # Enable dynamic backchannel hostname so Keycloak returns the internal service URL
        # (not KC_HOSTNAME) for backend-to-backend OIDC discovery requests
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                textwrap.dedent("""\
                    kubectl --kubeconfig=/kubeconfig -n keycloak set env statefulset/keycloak KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true
                    kubectl --kubeconfig=/kubeconfig -n keycloak rollout status statefulset/keycloak --timeout=300s
                """),
            ],
            "Enabling Keycloak backchannel dynamic hostname",
        )
        await run_in_vm(
            vm_name,
            [
                "helm",
                "upgrade",
                "--install",
                "kagenti",
                "oci://ghcr.io/kagenti/kagenti/kagenti",
                f"--version={kagenti_chart_version}",
                "--namespace=kagenti-system",
                "--create-namespace",
                "--values=/tmp/kagenti-values.yaml",
                "--timeout=10m",
                "--kubeconfig=/kubeconfig",
                *(f"--set={v}" for v in scoped_sets["kagenti"]),
            ],
            "Installing kagenti platform (operator + backend)",
        )
        # Label namespaces for shared gateway access and create agentstack HTTPRoutes
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                textwrap.dedent("""\
                    KC=/kubeconfig
                    # Ensure the agentstack namespace exists before creating HTTPRoutes
                    kubectl --kubeconfig=$KC create namespace agentstack --dry-run=client -o yaml | kubectl --kubeconfig=$KC apply -f -
                    # Label namespaces so the Gateway allows HTTPRoutes from them
                    for ns in agentstack keycloak kagenti-system istio-system; do
                        kubectl --kubeconfig=$KC label namespace $ns shared-gateway-access=true --overwrite
                    done
                    # Create HTTPRoutes for agentstack services through the shared gateway
                    cat <<'EOF' | kubectl --kubeconfig=$KC apply -f -
                    apiVersion: gateway.networking.k8s.io/v1
                    kind: HTTPRoute
                    metadata:
                      name: agentstack-ui
                      namespace: agentstack
                    spec:
                      parentRefs:
                        - name: http
                          namespace: kagenti-system
                      hostnames:
                        - "agentstack.localtest.me"
                      rules:
                        - backendRefs:
                            - name: agentstack-ui-svc
                              port: 8334
                    ---
                    apiVersion: gateway.networking.k8s.io/v1
                    kind: HTTPRoute
                    metadata:
                      name: agentstack-api
                      namespace: agentstack
                    spec:
                      parentRefs:
                        - name: http
                          namespace: kagenti-system
                      hostnames:
                        - "agentstack-api.localtest.me"
                      rules:
                        - backendRefs:
                            - name: agentstack-server-svc
                              port: 8333
                    ---
                    apiVersion: gateway.networking.k8s.io/v1
                    kind: HTTPRoute
                    metadata:
                      name: otel-collector
                      namespace: kagenti-system
                    spec:
                      parentRefs:
                        - name: http
                          namespace: kagenti-system
                      hostnames:
                        - "otel-collector.localtest.me"
                      rules:
                        - backendRefs:
                            - name: otel-collector
                              port: 8335
                    EOF
                """),
            ],
            "Configuring gateway routes for agentstack services",
        )

        # --- Agentstack helm install ---
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                "timeout 5m bash -c 'until kubectl --kubeconfig=/kubeconfig get nodes --no-headers -o custom-columns=NAME:.metadata.name 2>/dev/null | grep -q .; do sleep 5; done' && "
                "kubectl --kubeconfig=/kubeconfig get nodes --no-headers -o custom-columns=NAME:.metadata.name | xargs -I {} sh -c \"grep -q '{}' /etc/hosts || echo '127.0.0.1 {}' >> /etc/hosts\"",
            ],
            "Ensuring node name resolution",
        )
        await run_in_vm(
            vm_name,
            [
                "helm",
                "upgrade",
                "--install",
                "agentstack",
                "/tmp/agentstack-chart.tgz",
                "--namespace=agentstack",
                "--create-namespace",
                "--values=/tmp/agentstack-values.yaml",
                "--timeout=20m",
                "--wait",
                "--kubeconfig=/kubeconfig",
                *(f"--set={v}" for v in scoped_sets["agentstack"]),
            ],
            "Deploying Agent Stack platform with Helm",
        )
        if shas_guest_before and (
            replaced_digests := set(shas_guest_before.values())
            - set((await detect_image_shas(vm_name, platform, loaded_images, mode="guest")).values())
        ):
            for pod in json.loads(
                (
                    await run_in_vm(
                        vm_name,
                        [
                            "kubectl",
                            "--kubeconfig=/kubeconfig",
                            "get",
                            "pods",
                            "-o",
                            "json",
                            "--all-namespaces",
                        ],
                        "Getting pods",
                    )
                ).stdout
            ).get("items", []):
                if any(
                    cs.get("imageID", "") in replaced_digests
                    for cs in pod.get("status", {}).get("containerStatuses", [])
                ):
                    await run_in_vm(
                        vm_name,
                        [
                            "kubectl",
                            "--kubeconfig=/kubeconfig",
                            "delete",
                            "pod",
                            pod["metadata"]["name"],
                            "-n",
                            pod["metadata"]["namespace"],
                        ],
                        f"Removing pod with obsolete image {pod['metadata']['namespace']}/{pod['metadata']['name']}",
                    )
        if platform == "microshift":
            await run_in_vm(
                vm_name,
                [
                    "timeout",
                    "5m",
                    "bash",
                    "-c",
                    "until kubectl --kubeconfig=/kubeconfig wait --for=condition=Ready pod -n openshift-dns -l dns.operator.openshift.io/daemonset-dns=default --timeout=2m; do sleep 5; done",
                ],
                "Waiting for DNS to be ready",
            )
        await run_in_vm(
            vm_name,
            ["bash"],
            "Forwarding VM services to host",
            input=textwrap.dedent("""\
                    set -euxo pipefail
                    systemctl daemon-reload
                    # Forward the Istio gateway on port 8080 — all services route through it via hostnames
                    # (keycloak.localtest.me, agentstack.localtest.me, kagenti-ui.localtest.me, etc.)
                    systemctl start "kubectl-port-forward@kagenti-system:http-istio:8080:80" &
                    # Forward OTel collector directly (kagenti-system namespace, not routed through gateway)
                    systemctl start "kubectl-port-forward@kagenti-system:otel-collector:4318" &
                """)
            .strip()
            .encode(),
        )

        if not no_wait_for_platform:
            with console.status("Waiting for Agent Stack platform to be ready...", spinner="dots"):
                async with httpx.AsyncClient() as client:
                    try:
                        async for attempt in AsyncRetrying(
                            stop=stop_after_delay(datetime.timedelta(minutes=20)),
                            wait=wait_fixed(datetime.timedelta(seconds=1)),
                            retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
                            reraise=True,
                        ):
                            with attempt:
                                (await client.get("http://agentstack-api.localtest.me:8080/healthcheck")).raise_for_status()
                    except Exception as ex:
                        raise ConnectionError(
                            "Server did not start in 20 minutes. Please check your internet connection."
                        ) from ex

        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                "kubectl --kubeconfig=/kubeconfig wait --for=condition=Complete job/keycloak-provision -n agentstack --timeout=300s",
            ],
            "Waiting for Keycloak provisioning to complete",
        )
        console.success("Agent Stack platform started successfully!")
        phoenix_enabled = any("components.otel.enabled=true" in v.lower() for v in scoped_sets.get("kagenti-deps", []))
        if phoenix_enabled:
            console.print(
                textwrap.dedent("""\

                License Notice:
                Phoenix (provided by kagenti) is licensed under the Elastic License v2 (ELv2),
                which has specific terms regarding commercial use and distribution. By using this platform,
                you acknowledge compliance with the ELv2 license terms.
                See: https://github.com/Arize-ai/phoenix/blob/main/LICENSE
                """),
                style="dim",
            )

        if not skip_login:
            await agentstack_cli.commands.server.server_login("http://agentstack-api.localtest.me:8080")


#     ######  ########  #######  ########
#    ##    ##    ##    ##     ## ##     ##
#    ##          ##    ##     ## ##     ##
#     ######     ##    ##     ## ########
#          ##    ##    ##     ## ##
#    ##    ##    ##    ##     ## ##
#     ######     ##     #######  ##


@app.command("stop", help="Stop Agent Stack platform. [Local only]")
async def stop_cmd(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        if not await detect_vm_status(vm_name):
            console.info("Agent Stack platform not found. Nothing to stop.")
            return
        if detect_driver() == "lima":
            await run_command(
                [detect_limactl(), "--tty=false", "stop", "--force", vm_name],
                "Stopping Agent Stack VM",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )
        else:
            await run_command(["wsl.exe", "--terminate", vm_name], "Stopping Agent Stack VM")
        console.success("Agent Stack platform stopped successfully.")


#    ########  ######## ##       ######## ######## ########
#    ##     ## ##       ##       ##          ##    ##
#    ##     ## ##       ##       ##          ##    ##
#    ##     ## ######   ##       ######      ##    ######
#    ##     ## ##       ##       ##          ##    ##
#    ##     ## ##       ##       ##          ##    ##
#    ########  ######## ######## ########    ##    ########


@app.command("delete", help="Delete Agent Stack platform. [Local only]")
async def delete_cmd(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        if detect_driver() == "lima":
            await run_command(
                [detect_limactl(), "--tty=false", "delete", "--force", vm_name],
                "Deleting Agent Stack platform",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                check=False,
                cwd="/",
            )
        else:
            await run_command(["wsl.exe", "--unregister", vm_name], "Deleting Agent Stack platform", check=False)
        console.success("Agent Stack platform deleted successfully.")


#    #### ##     ## ########   #######  ########  ########
#     ##  ###   ### ##     ## ##     ## ##     ##    ##
#     ##  #### #### ##     ## ##     ## ##     ##    ##
#     ##  ## ### ## ########  ##     ## ########     ##
#     ##  ##     ## ##        ##     ## ##   ##      ##
#     ##  ##     ## ##        ##     ## ##    ##     ##
#    #### ##     ## ##         #######  ##     ##    ##


@app.command("import", help="Import a local docker image into the Agent Stack platform. [Local only]")
async def import_cmd(
    tag: typing.Annotated[str, typer.Argument(help="Docker image tag to import")],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        if (await detect_vm_status(vm_name)) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        platform = (
            (
                await run_in_vm(
                    vm_name,
                    [
                        "bash",
                        "-c",
                        "systemctl is-active --quiet k3s && echo k3s || systemctl is-active --quiet microshift && echo microshift || exit 1",
                    ],
                    "Detecting Kubernetes platform",
                )
            )
            .stdout.decode()
            .strip()
        )
        host_path, guest_path = detect_export_import_paths()
        try:
            await run_command(["docker", "image", "save", "-o", host_path, tag], f"Exporting image {tag} from Docker")
            await run_in_vm(
                vm_name,
                ["k3s", "ctr", "images", "import", guest_path]
                if platform == "k3s"
                else ["skopeo", "copy", f"docker-archive:{guest_path}:{tag}", f"containers-storage:{tag}"],
                f"Importing image {tag} into Agent Stack platform",
            )
        finally:
            await anyio.Path(host_path).unlink(missing_ok=True)


#    ######## ##     ## ########  ######
#    ##        ##   ##  ##       ##    ##
#    ##         ## ##   ##       ##
#    ######      ###    ######   ##
#    ##         ## ##   ##       ##
#    ##        ##   ##  ##       ##    ##
#    ######## ##     ## ########  ######


@app.command("exec", help="For debugging -- execute a command inside the Agent Stack platform VM. [Local only]")
async def exec_cmd(
    command: typing.Annotated[list[str] | None, typer.Argument()] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose, show_success_status=False):
        if (await detect_vm_status(vm_name)) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        if detect_driver() == "lima":
            await anyio.run_process(
                [detect_limactl(), "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--", "sudo", *(command or ["/bin/bash"])],
                check=False,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                env={**os.environ, "LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )
        else:
            await anyio.run_process(
                ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", *(command or ["/bin/bash"])],
                check=False,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                cwd="/",
            )
