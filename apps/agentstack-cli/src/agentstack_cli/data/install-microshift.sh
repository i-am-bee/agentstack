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

    echo "deb [signed-by=${gpgkey}] $(dirname "${relkey}") /" > \
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