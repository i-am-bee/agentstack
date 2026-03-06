#!/bin/bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

echo net.ipv4.ip_forward=1 >> /etc/sysctl.conf
mkdir -p -m 777 /postgresql-data /seaweedfs-data /registry-data /redis-data

apt-mark auto $(apt-mark showmanual)
apt-get update -y -q
apt-get install -y -q --no-install-recommends \
    containernetworking-plugins \
    cri-o \
    cri-tools \
    kubectl \
    skopeo \
    sshfs
sudo apt-mark manual \
    cloud-init \
    dbus \
    dhcpcd \
    iproute2 \
    iptables \
    linux-image-cloud-$(uname -m | sed -e 's/aarch64/arm64/;s/x86_64/amd64/') \
    openssh-server \
    sudo \
    systemd \
    systemd-sysv

curl -fsSL "https://github.com/microshift-io/microshift/releases/download/4.21.0_g29f429c21_4.21.0_okd_scos.ec.15/microshift-debs-$(uname -m | sed -e 's/arm64/aarch64/;s/amd64/x86_64/').tgz" | tar -xz -C /tmp
dpkg -i /tmp/microshift_*.deb /tmp/microshift-kindnet_*.deb
ln -sf /var/lib/microshift/resources/kubeadmin/kubeconfig /kubeconfig

ARCH_HELM=$(uname -m | sed -e 's/aarch64/arm64/;s/x86_64/amd64/')
curl -fsSL "https://get.helm.sh/helm-v4.1.1-linux-${ARCH_HELM}.tar.gz" | tar -xzf - --strip-components=1 -C /usr/local/bin "linux-${ARCH_HELM}/helm"
chmod +x /usr/local/bin/helm

systemctl enable crio
systemctl enable microshift
systemctl stop microshift
systemctl stop crio

apt-get purge --auto-remove -y --allow-remove-essential \
    apt \
    bash-completion \
    groff-base \
    man-db \
    manpages

passwd -l root
cloud-init clean --logs
rm -rf \
    /etc/apt/sources.list.d/* \
    /root/.cache \
    /tmp/* \
    /usr/bin/apt* \
    /usr/share/doc/* \
    /usr/share/groff/* \
    /usr/share/i18n/* \
    /usr/share/info/* \
    /usr/share/linda/* \
    /usr/share/lintian/* \
    /usr/share/locale/* \
    /usr/share/man/* \
    /usr/share/vim/* \
    /var/cache/apt/* \
    /var/lib/apt/* \
    /var/lib/dpkg/* \
    /var/lib/microshift/* \
    /var/tmp/* \
    /lib/firmware/*

find /usr/share/locale -mindepth 1 -maxdepth 1 ! -name 'en*' -exec rm -rf {} +
find /var/log -type f -exec truncate -s 0 {} +

truncate -s 0 /etc/machine-id
