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

# Check if k3s is already installed (for backward compatibility with old VMs)
if systemctl is-enabled k3s &>/dev/null; then
    echo "k3s is already installed (legacy VM), ensuring it is started..."
    systemctl start k3s || true
    exit 0
fi

# Check if MicroShift is already installed
if systemctl is-enabled microshift &>/dev/null; then
    echo "MicroShift is already installed, ensuring it is started..."
    systemctl start microshift || true
    exit 0
fi

echo "Installing MicroShift..."

# Determine architecture
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)
        MICROSHIFT_ARCH="x86_64"
        ;;
    aarch64)
        MICROSHIFT_ARCH="aarch64"
        ;;
    *)
        echo "ERROR: Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# MicroShift release version and download URL
MICROSHIFT_VERSION="4.21.0_g29f429c21_4.21.0_okd_scos.ec.15"
MICROSHIFT_URL="https://github.com/microshift-io/microshift/releases/download/${MICROSHIFT_VERSION}/microshift-debs-${MICROSHIFT_ARCH}.tgz"

# Download and extract MicroShift DEBs
WORK_DIR="/tmp/microshift-install"
mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

echo "Downloading MicroShift release ${MICROSHIFT_VERSION}..."
curl -fsSL "${MICROSHIFT_URL}" -o microshift-debs.tgz

echo "Extracting MicroShift packages..."
tar -xzf microshift-debs.tgz

# Helper function to find the latest available version of a DEB package
function find_debpkg_version() {
    local debpkg="$1"
    local version="$2"
    local relkey_base="$3"

    for _ in 1 2 3 ; do
        local relkey
        relkey="${relkey_base}/v${version}/deb/Release.key"
        if ! curl -fsSL "${relkey}" -o /dev/null 2>/dev/null ; then
            echo "WARNING: The ${debpkg} package version '${version}' not found. Trying previous version." >&2
            local xver="${version%%.*}"
            local yver="${version#*.}"
            if [ "${yver}" -lt 1 ] ; then
                echo "ERROR: Cannot decrement minor version below 0" >&2
                break
            fi
            version="${xver}.$(( yver - 1 ))"
        else
            echo "Found '${debpkg}' package version '${version}'" >&2
            echo "${version}"
            return
        fi
    done

    echo "ERROR: Failed to find '${debpkg}' package in repository" >&2
    exit 1
}

# Helper function for installing a DEB package from a repository
function install_debpkg() {
    local debpkg="$1"
    local version="$2"
    local relkey="$3"
    local extra_packages="${4:-}"

    local -r outname="${debpkg}-${version}"
    local -r gpgkey="/etc/apt/keyrings/${outname}-apt-keyring.gpg"

    rm -f "${gpgkey}"
    curl -fsSL "${relkey}" | gpg --batch --dearmor -o "${gpgkey}"

    echo "deb [signed-by=${gpgkey}] $(dirname "${relkey}") /" > \\
        "/etc/apt/sources.list.d/${outname}.list"

    apt-get update -y -q
    apt-get install -y -q --allow-downgrades "${debpkg}=${version}*" ${extra_packages}
}

# Install prerequisites
echo "Installing prerequisites..."
export DEBIAN_FRONTEND=noninteractive
export TZ=Etc/UTC
apt-get update -y -q
apt-get install -y -q tzdata curl gnupg podman

# Install and configure firewall
echo "Configuring firewall..."
apt-get install -y -q ufw
ufw --force enable
ufw allow from 10.42.0.0/16
ufw route allow from 10.42.0.0/16
ufw allow from 169.254.169.1
ufw allow ssh

# Install CRI-O
echo "Installing CRI-O..."
source "${WORK_DIR}/dependencies.txt"

CRIO_VERSION_FOUND="$(find_debpkg_version "cri-o" "${CRIO_VERSION}" "https://pkgs.k8s.io/addons:/cri-o:/stable:")"
CRIO_RELKEY="https://pkgs.k8s.io/addons:/cri-o:/stable:/v${CRIO_VERSION_FOUND}/deb/Release.key"
install_debpkg "cri-o" "${CRIO_VERSION_FOUND}" "${CRIO_RELKEY}" "crun containernetworking-plugins"

# Disable default CNI configs to allow Kindnet override
find /etc/cni/net.d -name '*.conflist' -print 2>/dev/null | while read -r cl ; do
    mv "${cl}" "${cl}.disabled"
done

# Configure CRI-O to use the CNI plugin directory
CNI_DIR="$(dpkg -L containernetworking-plugins | grep -E '/portmap$' | tail -1 | xargs dirname)"
mkdir -p /etc/crio/crio.conf.d
cat > /etc/crio/crio.conf.d/14-microshift-cni.conf <<EOF
[crio.network]
plugin_dirs = [
    "${CNI_DIR}",
]
EOF

# Configure CRI-O registry settings for insecure registries (before first start)
mkdir -p /etc/containers/registries.conf.d
cat > /etc/containers/registries.conf.d/200-microshift-local.conf <<EOF
# Configuration for local insecure registry (to be used by Agent Stack)
[[registry]]
location = "agentstack-registry-svc.default:5001"
insecure = true

[[registry.mirror]]
location = "localhost:30501"
insecure = true
EOF

systemctl daemon-reload
systemctl enable crio
systemctl start crio

# Install kubectl and cri-tools
echo "Installing kubectl and CLI tools..."
KUBECTL_VERSION_FOUND="$(find_debpkg_version "kubectl" "${CRIO_VERSION}" "https://pkgs.k8s.io/core:/stable:")"
KUBECTL_RELKEY="https://pkgs.k8s.io/core:/stable:/v${KUBECTL_VERSION_FOUND}/deb/Release.key"
install_debpkg "kubectl" "${KUBECTL_VERSION_FOUND}" "${KUBECTL_RELKEY}" "cri-tools"

echo "Installing MicroShift packages..."
find "${WORK_DIR}" -maxdepth 1 -name 'microshift*.deb' -print 2>/dev/null | sort | while read -r deb_package; do
    dpkg -i "${deb_package}"
done
apt-get install -y -q -f

systemctl enable microshift

# Configure MicroShift to use port 16443 (instead of default 6443)
echo "Configuring MicroShift..."
mkdir -p /etc/microshift
cat > /etc/microshift/config.yaml <<EOF
apiServer:
    port: 16443
EOF

# Create registry data directory for Agent Stack internal registry
mkdir -p /registry-data
chmod 755 /registry-data

# Configure TopoLVM storage with a loopback device for development
# MicroShift uses TopoLVM/LVMS which requires LVM volume groups
echo "Configuring storage..."

# Install LVM tools if not present
apt-get install -y -q lvm2

if ! vgs myvg1 &>/dev/null; then
    # Create a sparse 50GB loopback file for storage (doesn't consume full space immediately)
    truncate -s 50G /var/lib/microshift-storage.img

    # Set up loopback device
    LOOP_DEV=$(losetup -f)
    losetup "$LOOP_DEV" /var/lib/microshift-storage.img

    # Create physical volume and volume group
    # Using 'myvg1' to match MicroShift's default LVMS configuration
    pvcreate "$LOOP_DEV"
    vgcreate myvg1 "$LOOP_DEV"

    echo "Created volume group myvg1 on $LOOP_DEV"
    vgs myvg1

    # Create systemd service to set up loopback device on boot
    cat > /etc/systemd/system/microshift-storage-loopback.service <<'SYSTEMD_EOF'
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
SYSTEMD_EOF

    systemctl enable microshift-storage-loopback.service
fi

echo "Storage configuration complete"
vgs
lvs

# Start MicroShift
echo "Starting MicroShift..."
systemctl start microshift

# Wait for MicroShift to be ready
echo "Waiting for MicroShift to initialize (this may take several minutes)..."
timeout 600s bash -c 'until test -f /var/lib/microshift/resources/kubeadmin/kubeconfig; do sleep 5; done' || {
    echo "ERROR: MicroShift did not initialize in time"
    echo "Check logs with: journalctl -u microshift -n 100"
    exit 1
}

# Adjust kubeconfig permissions
chmod 644 /var/lib/microshift/resources/kubeadmin/kubeconfig

# Clean up
cd /
rm -rf "${WORK_DIR}"

echo "MicroShift installation completed successfully!"
"""


class ImagePullMode(StrEnum):
    guest = "guest"
    host = "host"
    hybrid = "hybrid"
    skip = "skip"


# ============================================================================
# DRIVER DETECTION
# ============================================================================


@functools.cache
def detect_driver() -> typing.Literal["lima", "wsl"]:
    """Detect which VM driver to use (Lima or WSL)"""
    has_lima = (importlib.resources.files("agentstack_cli") / "data" / "limactl").is_file() or shutil.which("limactl")
    has_vz = os.path.exists("/System/Library/Frameworks/Virtualization.framework")
    arch = "aarch64" if platform_module.machine().lower() == "arm64" else platform_module.machine().lower()
    has_qemu = bool(shutil.which(f"qemu-system-{arch}"))

    if platform_module.system() == "Windows" or shutil.which("wsl.exe"):
        return "wsl"
    elif has_lima and (has_vz or has_qemu):
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
            if not has_qemu:
                console.hint(
                    f"QEMU is needed on Linux, please install it and ensure that qemu-system-{arch} is in PATH. Refer to https://www.qemu.org/download/ for instructions."
                )
        sys.exit(1)


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
    driver = detect_driver()

    if driver == "lima":
        bundled_limactl = importlib.resources.files("agentstack_cli") / "data" / "limactl"
        limactl_exe = str(bundled_limactl) if bundled_limactl.is_file() else str(shutil.which("limactl"))
        return await run_command(
            [limactl_exe, "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--", "sudo", *command],
            message,
            env={"LIMA_HOME": str(Configuration().lima_home)} | (env or {}),
            cwd="/",
            input=input,
            check=check,
        )
    else:  # wsl
        return await run_command(
            ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", *command],
            message,
            env={**(env or {}), "WSL_UTF8": "1", "WSLENV": os.getenv("WSLENV", "") + ":WSL_UTF8"},
            input=input,
            check=check,
        )


async def get_vm_status(vm_name: str) -> typing.Literal["running"] | str | None:
    """Get VM status"""
    driver = detect_driver()

    try:
        if driver == "lima":
            bundled_limactl = importlib.resources.files("agentstack_cli") / "data" / "limactl"
            limactl_exe = str(bundled_limactl) if bundled_limactl.is_file() else str(shutil.which("limactl"))
            result = await run_command(
                [limactl_exe, "--tty=false", "list", "--format=json"],
                "Looking for existing Agent Stack platform in Lima",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )

            for line in result.stdout.decode().split("\n"):
                if not line:
                    continue
                Status = typing.TypedDict("Status", {"name": str, "status": str})
                status = pydantic.TypeAdapter(Status).validate_json(line)
                if status["name"] == vm_name:
                    return status["status"].lower()
            return None
        else:  # wsl
            for status, cmd in [("running", ["--running"]), ("stopped", [])]:
                result = await run_command(
                    ["wsl.exe", "--list", "--quiet", *cmd],
                    f"Looking for {status} Agent Stack platform in WSL",
                    env={"WSL_UTF8": "1", "WSLENV": os.getenv("WSLENV", "") + ":WSL_UTF8"},
                )
                if vm_name in result.stdout.decode().splitlines():
                    return status
            return None
    except Exception:
        return None


async def stop_vm(vm_name: str) -> None:
    """Stop VM"""
    driver = detect_driver()

    if driver == "lima":
        bundled_limactl = importlib.resources.files("agentstack_cli") / "data" / "limactl"
        limactl_exe = str(bundled_limactl) if bundled_limactl.is_file() else str(shutil.which("limactl"))
        await run_command(
            [limactl_exe, "--tty=false", "stop", "--force", vm_name],
            "Stopping Agent Stack VM",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
    else:  # wsl
        await run_command(["wsl.exe", "--terminate", vm_name], "Stopping Agent Stack VM")


async def delete_vm(vm_name: str) -> None:
    """Delete VM"""
    driver = detect_driver()

    if driver == "lima":
        bundled_limactl = importlib.resources.files("agentstack_cli") / "data" / "limactl"
        limactl_exe = str(bundled_limactl) if bundled_limactl.is_file() else str(shutil.which("limactl"))
        await run_command(
            [limactl_exe, "--tty=false", "delete", "--force", vm_name],
            "Deleting Agent Stack platform",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            check=False,
            cwd="/",
        )
    else:  # wsl
        await run_command(["wsl.exe", "--unregister", vm_name], "Deleting Agent Stack platform", check=False)


async def exec_in_vm(vm_name: str, command: list[str]) -> None:
    """Execute command interactively in VM"""
    driver = detect_driver()

    if driver == "lima":
        bundled_limactl = importlib.resources.files("agentstack_cli") / "data" / "limactl"
        limactl_exe = str(bundled_limactl) if bundled_limactl.is_file() else str(shutil.which("limactl"))
        await anyio.run_process(
            [limactl_exe, "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--", *command],
            check=False,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env={**os.environ, "LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
    else:  # wsl
        await anyio.run_process(
            ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", *command],
            check=False,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd="/",
        )


# ============================================================================
# VM CREATION
# ============================================================================


async def create_vm(vm_name: str) -> None:
    """Create VM if it doesn't exist"""
    driver = detect_driver()

    if driver == "lima":
        Configuration().home.mkdir(exist_ok=True)
        current_status = await get_vm_status(vm_name)

        if not current_status:
            bundled_limactl = importlib.resources.files("agentstack_cli") / "data" / "limactl"
            limactl_exe = str(bundled_limactl) if bundled_limactl.is_file() else str(shutil.which("limactl"))

            await run_command(
                [limactl_exe, "--tty=false", "delete", "--force", vm_name],
                "Cleaning up remains of previous instance",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                check=False,
                cwd="/",
            )

            await run_command(
                [limactl_exe, "--tty=false", "delete", "--force", "beeai-platform"],
                "Cleaning up remains of legacy instance",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                check=False,
                cwd="/",
            )

            import psutil

            total_memory_gib = typing.cast(int, psutil.virtual_memory().total / (1024**3))

            if total_memory_gib < 4:
                console.error("Not enough memory. Agent Stack platform requires at least 4 GB of RAM.")
                sys.exit(1)

            if total_memory_gib < 8:
                console.warning("Less than 8 GB of RAM detected. Performance may be degraded.")

            vm_memory_gib = round(min(8.0, max(3.0, total_memory_gib / 2)))

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete_on_close=False) as template_file:
                template_file.write(
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
                            "memory": f"{vm_memory_gib}GiB",
                        }
                    )
                )
                template_file.flush()
                template_file.close()
                await run_command(
                    [
                        limactl_exe,
                        "--tty=false",
                        "start",
                        str(template_file.name),
                        f"--name={vm_name}",
                    ],
                    "Creating a Lima VM",
                    env={"LIMA_HOME": str(Configuration().lima_home)},
                    cwd="/",
                )
        elif current_status != "running":
            bundled_limactl = importlib.resources.files("agentstack_cli") / "data" / "limactl"
            limactl_exe = str(bundled_limactl) if bundled_limactl.is_file() else str(shutil.which("limactl"))
            await run_command(
                [limactl_exe, "--tty=false", "start", vm_name],
                "Starting up",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
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


# ============================================================================
# PLATFORM DETECTION
# ============================================================================


async def detect_platform(vm_name: str) -> typing.Literal["k3s", "microshift"]:
    """Detect which Kubernetes platform is running"""
    k3s_check = await run_in_vm(
        vm_name,
        ["systemctl", "is-active", "k3s"],
        "Detecting Kubernetes platform",
        check=False,
    )
    return "k3s" if k3s_check.returncode == 0 else "microshift"


def get_kubeconfig_path(platform: typing.Literal["k3s", "microshift"]) -> str:
    """Get kubeconfig path for platform"""
    return {
        "microshift": "/var/lib/microshift/resources/kubeadmin/kubeconfig",
        "k3s": "/etc/rancher/k3s/k3s.yaml",
    }[platform]


# ============================================================================
# INSTALLATION AND DEPLOYMENT
# ============================================================================


async def install_tools(vm_name: str) -> typing.Literal["k3s", "microshift"]:
    """Install Kubernetes tools and return detected platform"""
    # Execute MicroShift installation script (handles k3s backward compatibility)
    await run_in_vm(
        vm_name,
        ["bash"],
        "Installing MicroShift (this may take several minutes)",
        input=INSTALL_MICROSHIFT_SCRIPT.encode(),
    )

    # Detect platform
    platform = await detect_platform(vm_name)

    # Install Helm
    await run_in_vm(
        vm_name,
        [
            "sh",
            "-c",
            "which helm || curl -sfL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
        ],
        "Installing Helm",
    )

    return platform


def _canonify(tag: str) -> str:
    """Add docker.io prefix if not present"""
    return tag if "." in tag.split("/")[0] else f"docker.io/{tag}"


def _get_export_import_paths(vm_name: str) -> tuple[str, str]:
    """Get temporary paths for image export/import"""
    driver = detect_driver()

    if driver == "lima":
        image_dir = pathlib.Path("/tmp/agentstack")
        image_dir.mkdir(exist_ok=True, parents=True)
        image_path = str(image_dir / f"{uuid.uuid4()}.tar")
        return (image_path, image_path)
    else:  # wsl
        fd, tmp_path = tempfile.mkstemp(suffix=".tar")
        os.close(fd)
        windows_path = str(pathlib.Path(tmp_path).resolve().absolute())
        wsl_path = f"/mnt/{windows_path[0].lower()}/{windows_path[2:].replace(chr(92), '/').removeprefix('/')}"
        return (windows_path, wsl_path)


async def _grab_image_shas(
    vm_name: str,
    platform: typing.Literal["k3s", "microshift"],
    loaded_images: set[str],
    *,
    mode: typing.Literal["guest", "host"],
) -> dict[str, str]:
    """Get image SHA digests from host or guest"""
    if mode == "host":
        output = (
            await run_command(
                ["docker", "images", "--digests"],
                "Listing host images",
            )
        ).stdout.decode()
        # docker format: IMAGE TAG DIGEST ID ...
        return {
            tag: sha
            for line in output.splitlines()[1:]
            if (x := line.split())
            and len(x) >= 4
            and (sha := x[2])  # DIGEST column
            and x[1] != "<none>"  # Skip images without tags
            and ((tag := _canonify(x[0] + ":" + x[1])) in loaded_images)
        }
    else:
        # Guest: use platform-specific command
        if platform == "k3s":
            # k3s ctr format: REF DIGEST SIZE PLATFORM ...
            output = (
                await run_in_vm(
                    vm_name,
                    ["k3s", "ctr", "image", "ls"],
                    "Listing guest images",
                )
            ).stdout.decode()
            return {
                tag: sha
                for line in output.splitlines()[1:]
                if (x := line.split())
                and len(x) >= 3
                and (sha := x[1])  # DIGEST column
                and ((tag := _canonify(x[0])) in loaded_images)  # REF already has tag
            }
        else:
            # MicroShift crictl format: IMAGE TAG DIGEST ID ...
            output = (
                await run_in_vm(
                    vm_name,
                    ["crictl", "images", "--digests"],
                    "Listing guest images",
                )
            ).stdout.decode()
            return {
                tag: sha
                for line in output.splitlines()[1:]
                if (x := line.split())
                and len(x) >= 4
                and (sha := x[2])  # DIGEST column
                and x[1] != "<none>"  # Skip images without tags
                and ((tag := _canonify(x[0] + ":" + x[1])) in loaded_images)
            }


async def import_images(vm_name: str, platform: typing.Literal["k3s", "microshift"], *tags: str) -> None:
    """Import images from host Docker into VM"""
    if not tags:
        return

    host_path, guest_path = _get_export_import_paths(vm_name)

    try:
        await run_command(
            ["docker", "image", "save", "-o", host_path, *tags],
            f"Exporting image{'' if len(tags) == 1 else 's'} {', '.join(tags)} from Docker",
        )

        if platform == "k3s":
            await run_in_vm(
                vm_name,
                ["/bin/sh", "-c", f"k3s ctr images import {guest_path}"],
                f"Importing image{'' if len(tags) == 1 else 's'} {', '.join(tags)} into Agent Stack platform",
            )
        else:
            await run_in_vm(
                vm_name,
                ["podman", "load", "-i", guest_path],
                f"Importing image{'' if len(tags) == 1 else 's'} {', '.join(tags)} into Agent Stack platform",
            )
    finally:
        await anyio.Path(host_path).unlink(missing_ok=True)


async def import_image_to_internal_registry(
    vm_name: str,
    tag: str,
    loaded_images: set[str] | None = None,
) -> None:
    """Import image from host Docker into internal registry"""
    if loaded_images is None:
        loaded_images = set()

    platform = await detect_platform(vm_name)
    kubeconfig_path = get_kubeconfig_path(platform)
    host_path, guest_path = _get_export_import_paths(vm_name)

    try:
        await run_command(
            ["docker", "image", "save", "-o", str(host_path), tag],
            f"Exporting image {tag} from Docker",
        )
        job_name = f"push-{uuid.uuid4().hex[:6]}"
        await run_in_vm(
            vm_name,
            ["kubectl", f"--kubeconfig={kubeconfig_path}", "apply", "-f", "-"],
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
                                            (image for image in loaded_images if "alpine/crane" in image),
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
                f"--kubeconfig={kubeconfig_path}",
                "wait",
                "--for=condition=complete",
                f"job/{job_name}",
                "--timeout=300s",
            ],
            "Waiting for push to complete",
        )
    finally:
        await anyio.Path(host_path).unlink(missing_ok=True)


async def deploy(
    vm_name: str,
    platform: typing.Literal["k3s", "microshift"],
    set_values_list: list[str],
    values_file: pathlib.Path | None = None,
    image_pull_mode: ImagePullMode = ImagePullMode.guest,
) -> None:
    """Deploy Agent Stack platform with Helm"""
    kubeconfig_path = get_kubeconfig_path(platform)

    # Prepare Helm chart
    await run_in_vm(
        vm_name,
        ["sh", "-c", "mkdir -p /tmp/agentstack && cat >/tmp/agentstack/chart.tgz"],
        "Preparing Helm chart",
        input=(importlib.resources.files("agentstack_cli") / "data" / "helm-chart.tgz").read_bytes(),
    )

    # Prepare values
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
        values = merge(values, yaml.safe_load(values_file.read_text()))

    await run_in_vm(
        vm_name,
        ["sh", "-c", "cat >/tmp/agentstack/values.yaml"],
        "Preparing Helm values",
        input=yaml.dump(values).encode("utf-8"),
    )

    # List necessary images
    loaded_images = {
        _canonify(typing.cast(str, yaml.safe_load(line)))
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

    # Handle image pulling/importing based on mode
    images_to_import_from_host = set[str]()
    shas_guest_before: dict[str, str] = {}

    if image_pull_mode in {ImagePullMode.host, ImagePullMode.hybrid}:
        shas_guest_before = await _grab_image_shas(vm_name, platform, loaded_images, mode="guest")
        shas_host = await _grab_image_shas(vm_name, platform, loaded_images, mode="host")

        if image_pull_mode == ImagePullMode.host and (images_to_pull := loaded_images - shas_host.keys()):
            for image in images_to_pull:
                await run_command(
                    ["docker", "pull", image],
                    f"Pulling image {image} on host",
                )
            shas_host = await _grab_image_shas(vm_name, platform, loaded_images, mode="host")

        images_to_import_from_host = dict(shas_host.items() - shas_guest_before.items()).keys() & loaded_images
        await import_images(vm_name, platform, *images_to_import_from_host)

    if image_pull_mode in {ImagePullMode.guest, ImagePullMode.hybrid}:
        for image in loaded_images - images_to_import_from_host:
            async for attempt in AsyncRetrying(stop=stop_after_attempt(5)):
                with attempt:
                    attempt_num = attempt.retry_state.attempt_number
                    if platform == "k3s":
                        await run_in_vm(
                            vm_name,
                            ["k3s", "ctr", "image", "pull", image],
                            f"Pulling image {image}" + (f" (attempt {attempt_num})" if attempt_num > 1 else ""),
                        )
                    else:
                        await run_in_vm(
                            vm_name,
                            ["crictl", "pull", image],
                            f"Pulling image {image}" + (f" (attempt {attempt_num})" if attempt_num > 1 else ""),
                        )

    # Copy kubeconfig
    kubeconfig_local_path = anyio.Path(Configuration().lima_home) / vm_name / "copied-from-guest" / "kubeconfig.yaml"
    await kubeconfig_local_path.parent.mkdir(parents=True, exist_ok=True)
    await kubeconfig_local_path.write_text(
        (
            await run_in_vm(
                vm_name,
                ["/bin/cat", kubeconfig_path],
                "Copying kubeconfig from Agent Stack platform",
            )
        ).stdout.decode()
    )

    # Wait for MicroShift-specific services
    if platform == "microshift":
        await run_in_vm(
            vm_name,
            [
                "bash",
                "-c",
                (
                    "for i in {1..120}; do "
                    f"if kubectl --kubeconfig={kubeconfig_path} "
                    "get endpoints -n topolvm-system topolvm-controller -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null | grep -q '.'; then "
                    "echo 'MicroShift is ready'; "
                    "exit 0; "
                    "fi; "
                    "echo 'Waiting for MicroShift services to be ready...'; "
                    "sleep 5; "
                    "done; "
                    "echo 'Timeout waiting for MicroShift'; "
                    "exit 1"
                ),
            ],
            "Waiting for MicroShift services to be ready",
        )

    # WSL-specific: Configure CoreDNS for MicroShift
    driver = detect_driver()
    if driver == "wsl" and platform == "microshift":
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
                f"""kubectl --kubeconfig={kubeconfig_path} get configmap -n openshift-dns dns-default -o yaml | \\
sed '/^  Corefile: |/a\\    host.docker.internal:53 {{\\n        hosts {{\\n            {host_ip} host.docker.internal\\n            fallthrough\\n        }}\\n    }}' | \\
kubectl --kubeconfig={kubeconfig_path} apply -f -""",
            ],
            "Setting up internal networking",
        )

        await run_in_vm(
            vm_name,
            [
                "kubectl",
                f"--kubeconfig={kubeconfig_path}",
                "delete",
                "pods",
                "-n",
                "openshift-dns",
                "-l",
                "dns.operator.openshift.io/daemonset-dns=default",
            ],
            "Restarting CoreDNS",
        )

    # Deploy with Helm
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
            f"--kubeconfig={kubeconfig_path}",
            *(f"--set={value}" for value in set_values_list),
        ],
        "Deploying Agent Stack platform with Helm",
    )

    # Restart pods with replaced images
    if shas_guest_before and (
        replaced_digests := set(shas_guest_before.values())
        - set((await _grab_image_shas(vm_name, platform, loaded_images, mode="guest")).values())
    ):
        for pod in dict.get(
            json.loads(
                (
                    await run_in_vm(
                        vm_name,
                        [
                            "kubectl",
                            f"--kubeconfig={kubeconfig_path}",
                            "get",
                            "pods",
                            "-o",
                            "json",
                            "--all-namespaces",
                        ],
                        "Getting pods",
                    )
                ).stdout
            ),
            "items",
            [],
        ):
            if any(
                container_status.get("imageID", "") in replaced_digests
                for container_status in pod.get("status", {}).get("containerStatuses", [])
            ):
                await run_in_vm(
                    vm_name,
                    [
                        "kubectl",
                        f"--kubeconfig={kubeconfig_path}",
                        "delete",
                        "pod",
                        pod["metadata"]["name"],
                        "-n",
                        pod["metadata"]["namespace"],
                    ],
                    f"Removing pod with obsolete image {pod['metadata']['namespace']}/{pod['metadata']['name']}",
                )

    # Set up port forwarding
    await run_in_vm(
        vm_name,
        ["sh", "-c", "cat >/etc/systemd/system/kubectl-port-forward@.service"],
        "Installing systemd unit for port-forwarding",
        input=textwrap.dedent(f"""\
        [Unit]
        Description=Kubectl Port Forward for service %i
        After=network.target

        [Service]
        Type=simple
        ExecStart=/bin/bash -c 'IFS=":" read svc port <<< "%i"; exec kubectl --kubeconfig={kubeconfig_path} port-forward --address=127.0.0.1 svc/$svc $port:$port'
        Restart=on-failure
        User=root

        [Install]
        WantedBy=multi-user.target
        """).encode(),
    )
    await run_in_vm(vm_name, ["systemctl", "daemon-reexec"], "Reloading systemd")

    services_json = (
        await run_in_vm(
            vm_name,
            [
                "kubectl",
                f"--kubeconfig={kubeconfig_path}",
                "get",
                "svc",
                "--field-selector=spec.type=LoadBalancer",
                "--output=json",
            ],
            "Detecting ports to forward",
        )
    ).stdout

    ServicePort = typing.TypedDict("ServicePort", {"port": int, "name": str})
    ServiceSpec = typing.TypedDict("ServiceSpec", {"ports": list[ServicePort]})
    ServiceMetadata = typing.TypedDict("ServiceMetadata", {"name": str, "namespace": str})
    Service = typing.TypedDict("Service", {"metadata": ServiceMetadata, "spec": ServiceSpec})
    Services = typing.TypedDict("Services", {"items": list[Service]})

    for service in pydantic.TypeAdapter(Services).validate_json(services_json)["items"]:
        name = service["metadata"]["name"]
        for port_item in service["spec"]["ports"]:
            port = port_item["port"]
            await run_in_vm(
                vm_name,
                ["systemctl", "enable", "--now", f"kubectl-port-forward@{name}:{port}.service"],
                f"Starting port-forward for {name}:{port}",
            )


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

    values_file_path = None
    if values_file:
        values_file_path = pathlib.Path(values_file)
        if not values_file_path.is_file():
            raise FileNotFoundError(f"Values file {values_file} not found.")

    with verbosity(verbose):
        await create_vm(vm_name)
        platform = await install_tools(vm_name)
        await deploy(
            vm_name,
            platform,
            set_values_list=set_values_list,
            values_file=values_file_path,
            image_pull_mode=image_pull_mode,
        )

        if not no_wait_for_platform:
            with console.status("Waiting for Agent Stack platform to be ready...", spinner="dots"):
                timeout = datetime.timedelta(minutes=20)
                async with httpx.AsyncClient() as client:
                    try:
                        async for attempt in AsyncRetrying(
                            stop=stop_after_delay(timeout),
                            wait=wait_fixed(datetime.timedelta(seconds=1)),
                            retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
                            reraise=True,
                        ):
                            with attempt:
                                resp = await client.get("http://localhost:8333/healthcheck")
                                resp.raise_for_status()
                    except Exception as ex:
                        raise ConnectionError(
                            f"Server did not start in {timeout}. Please check your internet connection."
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
        await stop_vm(vm_name)
        console.success("Agent Stack platform stopped successfully.")


@app.command("delete", help="Delete Agent Stack platform. [Local only]")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        await delete_vm(vm_name)
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
        platform = await detect_platform(vm_name)
        await import_images(vm_name, platform, tag)


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
        await exec_in_vm(vm_name, command or ["/bin/bash"])
