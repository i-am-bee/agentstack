# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import configparser
import datetime
import functools
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

import anyio
import httpx
import pydantic
import typer
import yaml
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
)

from agentstack_cli.async_typer import AsyncTyper
from agentstack_cli.configuration import Configuration
from agentstack_cli.console import console
from agentstack_cli.utils import merge, run_command, verbosity

app = AsyncTyper()
configuration = Configuration()

# ============================================================================
# CONSTANTS AND TYPES
# ============================================================================

INSTALL_MICROSHIFT_SCRIPT = """\
#!/bin/bash
set -eux -o pipefail

# Check for existing installations (k3s backward compatibility)
systemctl is-enabled k3s &>/dev/null && { systemctl start k3s || true; exit 0; }
systemctl is-enabled microshift &>/dev/null && { systemctl start microshift || true; exit 0; }

# Determine architecture
case "$(uname -m)" in
    x86_64) ARCH="x86_64" ;;
    aarch64) ARCH="aarch64" ;;
    *) echo "ERROR: Unsupported architecture"; exit 1 ;;
esac

# Download and extract MicroShift
VERSION="4.21.0_g29f429c21_4.21.0_okd_scos.ec.15"
WORK_DIR="/tmp/microshift-install"
mkdir -p "${WORK_DIR}" && cd "${WORK_DIR}"
curl -fsSL "https://github.com/microshift-io/microshift/releases/download/${VERSION}/microshift-debs-${ARCH}.tgz" | tar -xz

export DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC
apt-get update -y -q && apt-get install -y -q tzdata curl gnupg podman ufw lvm2

# Configure firewall
ufw --force enable && ufw allow from 10.42.0.0/16 && ufw route allow from 10.42.0.0/16 && ufw allow from 169.254.169.1 && ufw allow ssh

# Install CRI-O
source "${WORK_DIR}/dependencies.txt"
CRIO_VERSION_TAG="v${CRIO_VERSION}"
curl -fsSL "https://download.opensuse.org/repositories/isv:/cri-o:/stable:/${CRIO_VERSION_TAG}/deb/Release.key" | gpg --batch --dearmor -o /etc/apt/keyrings/cri-o-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/cri-o-apt-keyring.gpg] https://download.opensuse.org/repositories/isv:/cri-o:/stable:/${CRIO_VERSION_TAG}/deb/ /" > /etc/apt/sources.list.d/cri-o.list
apt-get update -y -q
apt-get install -y -q cri-o containernetworking-plugins

# Configure CNI and registries
find /etc/cni/net.d -name '*.conflist' 2>/dev/null | xargs -I{} mv {} {}.disabled
mkdir -p /etc/crio/crio.conf.d /etc/containers/registries.conf.d
CNI_DIR=$(dpkg -L containernetworking-plugins | grep -E '/portmap$' | tail -1 | xargs dirname)
cat > /etc/crio/crio.conf.d/14-microshift-cni.conf <<EOF
[crio.network]
plugin_dirs = ["${CNI_DIR}"]
EOF
cat > /etc/containers/registries.conf.d/200-microshift-local.conf <<EOF
[[registry]]
location = "agentstack-registry-svc.default:5001"
insecure = true
[[registry.mirror]]
location = "localhost:30501"
insecure = true
EOF

systemctl daemon-reload && systemctl enable --now crio

# Install kubectl and MicroShift
KUBERNETES_VERSION_TAG="v${CRIO_VERSION}"
curl -fsSL "https://pkgs.k8s.io/core:/stable:/${KUBERNETES_VERSION_TAG}/deb/Release.key" | gpg --batch --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/${KUBERNETES_VERSION_TAG}/deb/ /" > /etc/apt/sources.list.d/kubernetes.list
apt-get update -y -q
apt-get install -y -q kubectl cri-tools
find "${WORK_DIR}" -name 'microshift*.deb' | sort | xargs dpkg -i
apt-get install -y -q -f && systemctl enable microshift

# Configure MicroShift
mkdir -p /etc/microshift /registry-data
chmod 755 /registry-data
cat > /etc/microshift/config.yaml <<EOF
apiServer:
    port: 16443
EOF

# Configure storage
truncate -s 50G /var/lib/microshift-storage.img
LOOP_DEV=$(losetup -f)
losetup "$LOOP_DEV" /var/lib/microshift-storage.img
pvcreate "$LOOP_DEV" && vgcreate myvg1 "$LOOP_DEV"
cat > /etc/systemd/system/microshift-storage-loopback.service <<'EOF'
[Unit]
Description=Setup loopback device for MicroShift storage
DefaultDependencies=no
Before=lvm2-activation-early.service
After=local-fs-pre.target
Wants=local-fs-pre.target
[Service]
Type=oneshot
ExecStart=/bin/bash -c 'losetup -f /var/lib/microshift-storage.img || true'
RemainAfterExit=yes
[Install]
WantedBy=local-fs-pre.target
EOF
systemctl enable microshift-storage-loopback.service

# Start MicroShift
systemctl start microshift
cd / && rm -rf "${WORK_DIR}"
"""


class ImagePullMode(StrEnum):
    guest = "guest"
    host = "host"
    hybrid = "hybrid"
    skip = "skip"


# ============================================================================
# DRIVER DETECTION AND HELPERS
# ============================================================================


@functools.cache
def detect_driver() -> typing.Literal["lima", "wsl"]:
    """Detect which VM driver to use (Lima or WSL)"""
    has_lima = (importlib.resources.files("agentstack_cli") / "data" / "limactl").is_file() or shutil.which("limactl")
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
                    "This Linux distribution is not suppored by Lima VM binary releases (required: glibc>=2.34). Manually install Lima VM >=1.2.1 through either:\n"
                    + "  - Your distribution's package manager, if available (https://repology.org/project/lima/versions)\n"
                    + "  - Homebrew, which uses its own separate glibc on Linux (https://brew.sh)\n"
                    + "  - Building it yourself, and ensuring that limactl is in PATH (https://lima-vm.io/docs/installation/source/)"
                )
            if not shutil.which(f"qemu-system-{arch}"):
                console.hint(
                    f"QEMU is needed on Linux, please install it and ensure that qemu-system-{arch} is in PATH. Refer to https://www.qemu.org/download/ for instructions."
                )
        sys.exit(1)


@functools.cache
def get_limactl() -> str:
    """Get path to limactl executable"""
    bundled = importlib.resources.files("agentstack_cli") / "data" / "limactl"
    return str(bundled) if bundled.is_file() else str(shutil.which("limactl"))


# ============================================================================
# LOW-LEVEL VM OPERATIONS
# ============================================================================


async def run_in_vm(
    vm_name: str,
    command: list[str],
    message: str,
    env: dict[str, str] | None = None,
    input: bytes | None = None,
    check: bool = True,
) -> CompletedProcess[bytes]:
    """Execute command in VM (driver-agnostic)"""
    if detect_driver() == "lima":
        return await run_command(
            [get_limactl(), "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--", "sudo", *command],
            message,
            env={"LIMA_HOME": str(Configuration().lima_home)} | (env or {}),
            cwd="/",
            input=input,
            check=check,
        )
    return await run_command(
        ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", *command],
        message,
        env={**(env or {}), "WSL_UTF8": "1", "WSLENV": os.getenv("WSLENV", "") + ":WSL_UTF8"},
        input=input,
        check=check,
    )


async def get_vm_status(vm_name: str) -> typing.Literal["running"] | str | None:
    """Get VM status"""
    try:
        if detect_driver() == "lima":
            result = await run_command(
                [get_limactl(), "--tty=false", "list", "--format=json"],
                "Looking for existing Agent Stack platform",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )
            for line in result.stdout.decode().split("\n"):
                if (
                    line
                    and (status_data := pydantic.TypeAdapter(dict[str, str]).validate_json(line)).get("name") == vm_name
                ):
                    return status_data["status"].lower()
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
                    return status
    except Exception:
        pass
    return None


# ============================================================================
# PLATFORM DETECTION
# ============================================================================


async def detect_platform(vm_name: str) -> typing.Literal["k3s", "microshift"]:
    """Detect which Kubernetes platform is running"""
    return (
        "k3s"
        if (
            await run_in_vm(vm_name, ["systemctl", "is-active", "k3s"], "Detecting Kubernetes platform", check=False)
        ).returncode
        == 0
        else "microshift"
    )


# ============================================================================
# IMAGE OPERATIONS
# ============================================================================


def _get_export_import_paths(vm_name: str) -> tuple[str, str]:
    """Get temporary paths for image export/import"""
    if detect_driver() == "lima":
        image_dir = pathlib.Path("/tmp/agentstack")
        image_dir.mkdir(exist_ok=True, parents=True)
        path = str(image_dir / f"{uuid.uuid4()}.tar")
        return (path, path)
    fd, tmp_path = tempfile.mkstemp(suffix=".tar")
    os.close(fd)
    windows_path = str(pathlib.Path(tmp_path).resolve().absolute())
    return (windows_path, f"/mnt/{windows_path[0].lower()}/{windows_path[2:].replace(chr(92), '/').removeprefix('/')}")


async def _grab_image_shas(
    vm_name: str,
    platform: typing.Literal["k3s", "microshift"],
    loaded_images: set[str],
    *,
    mode: typing.Literal["guest", "host"],
) -> dict[str, str]:
    """Get image SHA digests from host or guest"""

    def canonify(t):
        return t if "." in t.split("/")[0] else f"docker.io/{t}"

    if mode == "host":
        lines = (
            (await run_command(["docker", "images", "--digests"], "Listing host images"))
            .stdout.decode()
            .splitlines()[1:]
        )
        return {
            canonify(f"{x[0]}:{x[1]}"): x[2]
            for line in lines
            if (x := line.split()) and len(x) >= 4 and x[1] != "<none>" and canonify(f"{x[0]}:{x[1]}") in loaded_images
        }

    if platform == "k3s":
        lines = (
            (await run_in_vm(vm_name, ["k3s", "ctr", "image", "ls"], "Listing guest images"))
            .stdout.decode()
            .splitlines()[1:]
        )
        return {
            canonify(x[0]): x[2]
            for line in lines
            if (x := line.split()) and len(x) >= 3 and canonify(x[0]) in loaded_images
        }

    lines = (
        (await run_in_vm(vm_name, ["crictl", "images", "--digests"], "Listing guest images"))
        .stdout.decode()
        .splitlines()[1:]
    )
    return {
        canonify(f"{x[0]}:{x[1]}"): x[2]
        for line in lines
        if (x := line.split()) and len(x) >= 4 and x[1] != "<none>" and canonify(f"{x[0]}:{x[1]}") in loaded_images
    }


async def import_image_to_internal_registry(vm_name: str, tag: str, loaded_images: set[str] | None = None) -> None:
    """Import image from host Docker into internal registry"""
    platform = await detect_platform(vm_name)
    kubeconfig = {
        "microshift": "/var/lib/microshift/resources/kubeadmin/kubeconfig",
        "k3s": "/etc/rancher/k3s/k3s.yaml",
    }[platform]
    host_path, guest_path = _get_export_import_paths(vm_name)
    try:
        await run_command(["docker", "image", "save", "-o", str(host_path), tag], f"Exporting image {tag} from Docker")
        job_name = f"push-{uuid.uuid4().hex[:6]}"
        await run_in_vm(
            vm_name,
            ["kubectl", f"--kubeconfig={kubeconfig}", "apply", "-f", "-"],
            "Starting push job",
            input=yaml.dump(
                {
                    "apiVersion": "batch/v1",
                    "kind": "Job",
                    "metadata": {"name": job_name, "namespace": "default"},
                    "spec": {
                        "backoffLimit": 0,
                        "ttlSecondsAfterFinished": 60,
                        "template": {
                            "spec": {
                                "restartPolicy": "Never",
                                "containers": [
                                    {
                                        "name": "crane",
                                        "image": next(
                                            (img for img in (loaded_images or set()) if "alpine/crane" in img),
                                            "ghcr.io/i-am-bee/alpine/crane:0.20.6",
                                        ),
                                        "command": [
                                            "crane",
                                            "push",
                                            f"/workspace/{pathlib.Path(host_path).name}",
                                            tag,
                                            "--insecure",
                                        ],
                                        "volumeMounts": [{"name": "workspace", "mountPath": "/workspace"}],
                                    }
                                ],
                                "volumes": [
                                    {
                                        "name": "workspace",
                                        "hostPath": {"path": str(pathlib.PurePosixPath(guest_path).parent)},
                                    }
                                ],
                            }
                        },
                    },
                }
            ).encode(),
        )
        await run_in_vm(
            vm_name,
            [
                "kubectl",
                f"--kubeconfig={kubeconfig}",
                "wait",
                "--for=condition=complete",
                f"job/{job_name}",
                "--timeout=300s",
            ],
            "Waiting for push to complete",
        )
    finally:
        await anyio.Path(host_path).unlink(missing_ok=True)


# ============================================================================
# CLI COMMANDS
# ============================================================================


@app.command("start", help="Start Agent Stack platform. [Local only]")
async def start(
    set_values_list: typing.Annotated[
        list[str], typer.Option("--set", help="Set Helm chart values using <key>=<value> syntax", default_factory=list)
    ],
    image_pull_mode: typing.Annotated[
        ImagePullMode,
        typer.Option(
            "--image-pull-mode",
            help=textwrap.dedent(
                """\
                guest = pull all images inside VM
                host = pull unavailable images on host, then import all
                hybrid = import available images from host, pull the rest in VM
                skip = skip explicit pull step (Kubernetes will attempt to pull missing images)
                """
            ),
        ),
    ] = ImagePullMode.guest,
    values_file: typing.Annotated[
        pathlib.Path | None, typer.Option("-f", help="Set Helm chart values using yaml values file")
    ] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
    skip_login: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    no_wait_for_platform: typing.Annotated[bool, typer.Option(hidden=True)] = False,
):
    import agentstack_cli.commands.server

    if values_file and not pathlib.Path(values_file).is_file():
        raise FileNotFoundError(f"Values file {values_file} not found.")

    with verbosity(verbose):
        # Create VM
        Configuration().home.mkdir(exist_ok=True)
        if detect_driver() == "lima":
            current_status = await get_vm_status(vm_name)
            lima_env = {"LIMA_HOME": str(Configuration().lima_home)}
            if not current_status:
                for legacy in [vm_name, "beeai-platform"]:
                    await run_command(
                        [get_limactl(), "--tty=false", "delete", "--force", legacy],
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
                with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete_on_close=False) as f:
                    f.write(
                        yaml.dump(
                            {
                                "images": [
                                    {
                                        "location": "https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img",
                                        "arch": "x86_64",
                                    },
                                    {
                                        "location": "https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-arm64.img",
                                        "arch": "aarch64",
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
                                    {"location": "/tmp/agentstack", "mountPoint": "/tmp/agentstack", "writable": True}
                                ],
                                "containerd": {"system": False, "user": False},
                                "hostResolver": {"hosts": {"host.docker.internal": "host.lima.internal"}},
                                "memory": f"{round(min(8.0, max(3.0, total_memory_gib / 2)))}GiB",
                            }
                        )
                    )
                    f.flush()
                    f.close()
                    await run_command(
                        [get_limactl(), "--tty=false", "start", f.name, f"--name={vm_name}"],
                        "Creating a Lima VM",
                        env=lima_env,
                        cwd="/",
                    )
            elif current_status != "running":
                await run_command(
                    [get_limactl(), "--tty=false", "start", vm_name], "Starting up", env=lima_env, cwd="/"
                )
            else:
                console.info("Updating an existing instance.")
        else:  # wsl
            if (await run_command(["wsl.exe", "--status"], "Checking for WSL2", check=False)).returncode != 0:
                console.error(
                    "WSL is not installed. Please follow the Agent Stack installation instructions: https://agentstack.beeai.dev/introduction/quickstart#windows"
                )
                console.hint(
                    "Run [green]wsl.exe --install[/green] as administrator. If you just did this, restart your PC and run the same command again. Full installation may require up to two restarts. WSL is properly set up once you reach a working Linux terminal. You can verify this by running [green]wsl.exe[/green] without arguments."
                )
                sys.exit(1)
            config_file = (
                pathlib.Path.home()
                if platform_module.system() == "Windows"
                else pathlib.Path(
                    (
                        await run_command(
                            ["/bin/sh", "-c", '''wslpath "$(cmd.exe /c 'echo %USERPROFILE%')"'''], "Detecting home path"
                        )
                    )
                    .stdout.decode()
                    .strip()
                )
            ) / ".wslconfig"
            config_file.touch()
            with config_file.open("r+") as f:
                config = configparser.ConfigParser()
                f.seek(0)
                config.read_file(f)
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
            if not await get_vm_status(vm_name):
                await run_command(
                    ["wsl.exe", "--unregister", vm_name], "Cleaning up remains of previous instance", check=False
                )
                await run_command(
                    ["wsl.exe", "--unregister", "beeai-platform"], "Cleaning up remains of legacy instance", check=False
                )
                await run_command(
                    ["wsl.exe", "--install", "--name", vm_name, "--no-launch", "--web-download"],
                    "Creating a WSL distribution",
                )
            await run_in_vm(
                vm_name,
                [
                    "sh",
                    "-c",
                    "echo '[network]\\ngenerateResolvConf = false\\n[boot]\\nsystemd=true\\n' >/etc/wsl.conf && rm /etc/resolv.conf && echo 'nameserver 1.1.1.1\\n' >/etc/resolv.conf && chattr +i /etc/resolv.conf",
                ],
                "Setting up DNS configuration",
                check=False,
            )
            await run_command(["wsl.exe", "--terminate", vm_name], "Restarting Agent Stack VM")
            await run_in_vm(vm_name, ["dbus-launch", "true"], "Ensuring persistence of Agent Stack VM")

        # Install tools and detect platform
        await run_in_vm(
            vm_name,
            ["bash"],
            "Installing MicroShift (this may take several minutes)",
            input=INSTALL_MICROSHIFT_SCRIPT.encode(),
        )
        platform = await detect_platform(vm_name)
        await run_in_vm(
            vm_name,
            [
                "sh",
                "-c",
                "which helm || curl -sfL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
            ],
            "Installing Helm",
        )

        # Deploy
        kubeconfig = {
            "microshift": "/var/lib/microshift/resources/kubeadmin/kubeconfig",
            "k3s": "/etc/rancher/k3s/k3s.yaml",
        }[platform]
        await run_in_vm(
            vm_name,
            ["sh", "-c", "mkdir -p /tmp/agentstack && cat >/tmp/agentstack/chart.tgz"],
            "Preparing Helm chart",
            input=(importlib.resources.files("agentstack_cli") / "data" / "helm-chart.tgz").read_bytes(),
        )
        values = {
            **{svc: {"service": {"type": "LoadBalancer"}} for svc in ["collector", "docling", "ui", "phoenix"]},
            "service": {"type": "LoadBalancer"},
            "externalRegistries": {"public_github": str(Configuration().agent_registry)},
            "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",
            "trustProxyHeaders": True,
            "keycloak": {
                "uiClientSecret": "agentstack-ui-secret",
                "serverClientSecret": "agentstack-server-secret",
                "service": {"type": "LoadBalancer"},
                "auth": {"adminPassword": "admin"},
            },
            "features": {"uiLocalSetup": True},
            "providerBuilds": {"enabled": True},
            "localDockerRegistry": {"enabled": True},
            "auth": {"enabled": False},
        }
        if values_file:
            values = merge(values, yaml.safe_load(pathlib.Path(values_file).read_text()))
        await run_in_vm(
            vm_name,
            ["sh", "-c", "cat >/tmp/agentstack/values.yaml"],
            "Preparing Helm values",
            input=yaml.dump(values).encode("utf-8"),
        )

        def canonify(t):
            return t if "." in t.split("/")[0] else f"docker.io/{t}"

        loaded_images = {
            canonify(typing.cast(str, yaml.safe_load(line)))
            for line in (
                await run_in_vm(
                    vm_name,
                    [
                        "/bin/bash",
                        "-c",
                        "helm template agentstack /tmp/agentstack/chart.tgz --values=/tmp/agentstack/values.yaml "
                        + " ".join(shlex.quote(f"--set={value}") for value in set_values_list)
                        + " | sed -n '/^\\s*image:/{ /{{/!{ s/.*image:\\s*//p } }'",
                    ],
                    "Listing necessary images",
                )
            )
            .stdout.decode()
            .splitlines()
        }
        images_to_import_from_host, shas_guest_before = set[str](), {}
        if image_pull_mode in {ImagePullMode.host, ImagePullMode.hybrid}:
            shas_guest_before = await _grab_image_shas(vm_name, platform, loaded_images, mode="guest")
            shas_host = await _grab_image_shas(vm_name, platform, loaded_images, mode="host")
            if image_pull_mode == ImagePullMode.host and (images_to_pull := loaded_images - shas_host.keys()):
                for image in images_to_pull:
                    await run_command(["docker", "pull", image], f"Pulling image {image} on host")
                shas_host = await _grab_image_shas(vm_name, platform, loaded_images, mode="host")
            images_to_import_from_host = dict(shas_host.items() - shas_guest_before.items()).keys() & loaded_images
            if images_to_import_from_host:
                host_path, guest_path = _get_export_import_paths(vm_name)
                try:
                    await run_command(
                        ["docker", "image", "save", "-o", host_path, *images_to_import_from_host],
                        f"Exporting image{'' if len(images_to_import_from_host) == 1 else 's'} {', '.join(images_to_import_from_host)} from Docker",
                    )
                    await run_in_vm(
                        vm_name,
                        ["/bin/sh", "-c", f"k3s ctr images import {guest_path}"]
                        if platform == "k3s"
                        else ["podman", "load", "-i", guest_path],
                        f"Importing image{'' if len(images_to_import_from_host) == 1 else 's'} {', '.join(images_to_import_from_host)} into Agent Stack platform",
                    )
                finally:
                    await anyio.Path(host_path).unlink(missing_ok=True)
        if image_pull_mode in {ImagePullMode.guest, ImagePullMode.hybrid}:
            for image in loaded_images - images_to_import_from_host:
                async for attempt in AsyncRetrying(stop=stop_after_attempt(5)):
                    with attempt:
                        await run_in_vm(
                            vm_name,
                            ["k3s", "ctr", "image", "pull", image] if platform == "k3s" else ["crictl", "pull", image],
                            f"Pulling image {image}"
                            + (
                                f" (attempt {attempt.retry_state.attempt_number})"
                                if attempt.retry_state.attempt_number > 1
                                else ""
                            ),
                        )
        kubeconfig_local = anyio.Path(Configuration().lima_home) / vm_name / "copied-from-guest" / "kubeconfig.yaml"
        await kubeconfig_local.parent.mkdir(parents=True, exist_ok=True)
        await kubeconfig_local.write_text(
            (
                await run_in_vm(vm_name, ["/bin/cat", kubeconfig], "Copying kubeconfig from Agent Stack platform")
            ).stdout.decode()
        )
        if platform == "microshift":
            await run_in_vm(
                vm_name,
                [
                    "bash",
                    "-c",
                    f"for i in {{1..120}}; do if kubectl --kubeconfig={kubeconfig} get endpoints -n topolvm-system topolvm-controller -o jsonpath='{{.subsets[*].addresses[*].ip}}' 2>/dev/null | grep -q '.'; then exit 0; fi; sleep 5; done; exit 1",
                ],
                "Waiting for MicroShift services to be ready",
            )
        if detect_driver() == "wsl" and platform == "microshift":
            host_ip = (
                (
                    await run_in_vm(
                        vm_name,
                        ["bash", "-c", "ip route show | grep -i default | cut -d' ' -f3"],
                        "Detecting host IP address",
                    )
                )
                .stdout.decode()
                .strip()
            )
            await run_in_vm(
                vm_name,
                [
                    "bash",
                    "-c",
                    f"kubectl --kubeconfig={kubeconfig} get configmap -n openshift-dns dns-default -o yaml | sed '/^  Corefile: |/a\\    host.docker.internal:53 {{\\n        hosts {{\\n            {host_ip} host.docker.internal\\n            fallthrough\\n        }}\\n    }}' | kubectl --kubeconfig={kubeconfig} apply -f -",
                ],
                "Setting up internal networking",
            )
            await run_in_vm(
                vm_name,
                [
                    "kubectl",
                    f"--kubeconfig={kubeconfig}",
                    "delete",
                    "pods",
                    "-n",
                    "openshift-dns",
                    "-l",
                    "dns.operator.openshift.io/daemonset-dns=default",
                ],
                "Restarting CoreDNS",
            )
        await run_in_vm(
            vm_name,
            [
                "helm",
                "upgrade",
                "--install",
                "agentstack",
                "/tmp/agentstack/chart.tgz",
                "--namespace=default",
                "--create-namespace",
                "--values=/tmp/agentstack/values.yaml",
                "--timeout=20m",
                "--wait",
                f"--kubeconfig={kubeconfig}",
                *(f"--set={value}" for value in set_values_list),
            ],
            "Deploying Agent Stack platform with Helm",
        )
        if shas_guest_before and (
            replaced_digests := set(shas_guest_before.values())
            - set((await _grab_image_shas(vm_name, platform, loaded_images, mode="guest")).values())
        ):
            for pod in json.loads(
                (
                    await run_in_vm(
                        vm_name,
                        ["kubectl", f"--kubeconfig={kubeconfig}", "get", "pods", "-o", "json", "--all-namespaces"],
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
                            f"--kubeconfig={kubeconfig}",
                            "delete",
                            "pod",
                            pod["metadata"]["name"],
                            "-n",
                            pod["metadata"]["namespace"],
                        ],
                        f"Removing pod with obsolete image {pod['metadata']['namespace']}/{pod['metadata']['name']}",
                    )
        await run_in_vm(
            vm_name,
            ["sh", "-c", "cat >/etc/systemd/system/kubectl-port-forward@.service"],
            "Installing systemd unit for port-forwarding",
            input=textwrap.dedent(
                f'[Unit]\nDescription=Kubectl Port Forward for service %i\nAfter=network.target\n\n[Service]\nType=simple\nExecStart=/bin/bash -c \'IFS=":" read svc port <<< "%i"; exec kubectl --kubeconfig={kubeconfig} port-forward --address=127.0.0.1 svc/$svc $port:$port\'\nRestart=on-failure\nUser=root\n\n[Install]\nWantedBy=multi-user.target\n'
            ).encode(),
        )
        await run_in_vm(vm_name, ["systemctl", "daemon-reexec"], "Reloading systemd")
        services_data: dict[str, typing.Any] = pydantic.TypeAdapter(dict[str, typing.Any]).validate_json(
            (
                await run_in_vm(
                    vm_name,
                    [
                        "kubectl",
                        f"--kubeconfig={kubeconfig}",
                        "get",
                        "svc",
                        "--field-selector=spec.type=LoadBalancer",
                        "--output=json",
                    ],
                    "Detecting ports to forward",
                )
            ).stdout
        )
        for service in services_data.get("items", []):
            for port_item in service["spec"]["ports"]:
                await run_in_vm(
                    vm_name,
                    [
                        "systemctl",
                        "enable",
                        "--now",
                        f"kubectl-port-forward@{service['metadata']['name']}:{port_item['port']}.service",
                    ],
                    f"Starting port-forward for {service['metadata']['name']}:{port_item['port']}",
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
                                (await client.get("http://localhost:8333/healthcheck")).raise_for_status()
                    except Exception as ex:
                        raise ConnectionError(
                            "Server did not start in 20 minutes. Please check your internet connection."
                        ) from ex

        console.success("Agent Stack platform started successfully!")
        if any("phoenix.enabled=true" in value.lower() for value in set_values_list):
            console.print(
                textwrap.dedent("""\

                License Notice:
                When you enable Phoenix, be aware that Arize Phoenix is licensed under the Elastic License v2 (ELv2),
                which has specific terms regarding commercial use and distribution. By enabling Phoenix, you acknowledge
                that you are responsible for ensuring compliance with the ELv2 license terms for your specific use case.
                Please review the Phoenix license (https://github.com/Arize-ai/phoenix/blob/main/LICENSE) before enabling
                this feature in production environments.
                """),
                style="dim",
            )

        if not skip_login:
            await agentstack_cli.commands.server.server_login("http://localhost:8333")


@app.command("stop", help="Stop Agent Stack platform. [Local only]")
async def stop(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        if not await get_vm_status(vm_name):
            console.info("Agent Stack platform not found. Nothing to stop.")
            return
        if detect_driver() == "lima":
            await run_command(
                [get_limactl(), "--tty=false", "stop", "--force", vm_name],
                "Stopping Agent Stack VM",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )
        else:
            await run_command(["wsl.exe", "--terminate", vm_name], "Stopping Agent Stack VM")
        console.success("Agent Stack platform stopped successfully.")


@app.command("delete", help="Delete Agent Stack platform. [Local only]")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        if detect_driver() == "lima":
            await run_command(
                [get_limactl(), "--tty=false", "delete", "--force", vm_name],
                "Deleting Agent Stack platform",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                check=False,
                cwd="/",
            )
        else:
            await run_command(["wsl.exe", "--unregister", vm_name], "Deleting Agent Stack platform", check=False)
        console.success("Agent Stack platform deleted successfully.")


@app.command("import", help="Import a local docker image into the Agent Stack platform. [Local only]")
async def import_image_cmd(
    tag: typing.Annotated[str, typer.Argument(help="Docker image tag to import")],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        if (await get_vm_status(vm_name)) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        platform = (
            "k3s"
            if (
                await run_in_vm(
                    vm_name, ["systemctl", "is-active", "k3s"], "Detecting Kubernetes platform", check=False
                )
            ).returncode
            == 0
            else "microshift"
        )
        host_path, guest_path = _get_export_import_paths(vm_name)
        try:
            await run_command(["docker", "image", "save", "-o", host_path, tag], f"Exporting image {tag} from Docker")
            await run_in_vm(
                vm_name,
                ["/bin/sh", "-c", f"k3s ctr images import {guest_path}"]
                if platform == "k3s"
                else ["podman", "load", "-i", guest_path],
                f"Importing image {tag} into Agent Stack platform",
            )
        finally:
            await anyio.Path(host_path).unlink(missing_ok=True)


@app.command("exec", help="For debugging -- execute a command inside the Agent Stack platform VM. [Local only]")
async def exec_cmd(
    command: typing.Annotated[list[str] | None, typer.Argument()] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose, show_success_status=False):
        if (await get_vm_status(vm_name)) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        if detect_driver() == "lima":
            await anyio.run_process(
                [get_limactl(), "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--", *(command or ["/bin/bash"])],
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
