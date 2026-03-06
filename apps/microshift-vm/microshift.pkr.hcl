packer {
  required_plugins {
    qemu = {
      version = "~> 1"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

variable "arch" {
  type    = string
  default = "aarch64"

  validation {
    condition     = contains(["x86_64", "aarch64"], var.arch)
    error_message = "Arch must be x86_64 or aarch64."
  }
}

variable "output_dir" {
  type    = string
  default = "dist"
}

variable "efi_code" {
  type        = string
  description = "Path to UEFI firmware code (read-only pflash)."
}

variable "efi_vars" {
  type        = string
  description = "Path to writable copy of UEFI vars pflash."
}

variable "accelerator" {
  type        = string
  default     = "kvm"
  description = "QEMU accelerator (kvm on Linux, hvf on macOS)."
}

locals {
  qemu_binary     = var.arch == "x86_64" ? "qemu-system-x86_64" : "qemu-system-aarch64"
  image_url       = var.arch == "x86_64" ? "https://cdimage.debian.org/cdimage/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2" : "https://cdimage.debian.org/cdimage/cloud/trixie/latest/debian-13-genericcloud-arm64.qcow2"
  image_checksum  = "file:https://cdimage.debian.org/cdimage/cloud/trixie/latest/SHA512SUMS"
  machine         = var.arch == "x86_64" ? "q35" : "virt"
}

source "qemu" "microshift" {
  iso_url      = local.image_url
  iso_checksum = local.image_checksum
  disk_image   = true
  disk_size    = "20G"

  qemu_binary  = local.qemu_binary
  machine_type = local.machine
  accelerator  = var.accelerator
  cpu_model    = "max"

  memory = 4096
  cpus   = 2

  headless = true

  ssh_username = "root"
  ssh_password = "packer"
  ssh_timeout  = "10m"

  shutdown_command = "shutdown -h now"

  cd_files = ["cloud-init/user-data", "cloud-init/meta-data"]
  cd_label = "cidata"

  efi_boot          = true
  efi_firmware_code = var.efi_code
  efi_firmware_vars = var.efi_vars

  output_directory = "${var.output_dir}/${var.arch}"
  vm_name          = "microshift-vm-${var.arch}.qcow2"

  format           = "qcow2"
  disk_compression = true
}

build {
  sources = ["source.qemu.microshift"]

  provisioner "file" {
    source      = "rootfs"
    destination = "/tmp"
  }

  provisioner "shell" {
    inline = ["cp -a /tmp/rootfs/. / && rm -rf /tmp/rootfs"]
  }

  provisioner "file" {
    source      = "install.sh"
    destination = "/tmp/install.sh"
  }

  provisioner "shell" {
    inline = ["bash /tmp/install.sh"]
  }

}
