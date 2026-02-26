#!/bin/bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

echo net.ipv4.ip_forward=1 >> /etc/sysctl.conf
mkdir -p -m 777 /postgresql-data /seaweedfs-data /registry-data /redis-data

apt-get update -y -q
apt-get install -y -q --no-install-recommends \
    containernetworking-plugins \
    cri-o \
    cri-tools \
    kubectl \
    skopeo

curl -fsSL "https://github.com/microshift-io/microshift/releases/download/4.21.0_g29f429c21_4.21.0_okd_scos.ec.15/microshift-debs-$(uname -m | sed -e 's/arm64/aarch64/' -e 's/amd64/x86_64/').tgz" | tar -xz -C /tmp
dpkg -i /tmp/microshift_*.deb /tmp/microshift-kindnet_*.deb
ln -sf /var/lib/microshift/resources/kubeadmin/kubeconfig /kubeconfig

ARCH_HELM=$(uname -m | sed -e 's/aarch64/arm64/' -e 's/x86_64/amd64/')
curl -fsSL "https://get.helm.sh/helm-v4.1.1-linux-${ARCH_HELM}.tar.gz" | tar -xzf - --strip-components=1 -C /usr/local/bin "linux-${ARCH_HELM}/helm"
chmod +x /usr/local/bin/helm

systemctl enable crio
systemctl enable microshift
systemctl stop microshift
systemctl stop crio

rm -rf /var/lib/microshift/*
cloud-init clean --logs
truncate -s 0 /etc/machine-id
