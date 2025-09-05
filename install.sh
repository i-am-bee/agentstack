#!/bin/sh
set -eu
echo "Starting the BeeAI Platform installation..."

# Install uv
if command -v uv >/dev/null 2>&1; then
    echo "uv is already installed."
else
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | UV_PRINT_QUIET=1 sh
fi

# Add uv installation paths to PATH
export PATH="$XDG_BIN_HOME:$XDG_DATA_HOME/../bin:$HOME/.local/bin:$PATH"

# Install beeai-cli
echo "Installing beeai-cli..."
uv tool install --quiet --force beeai-cli

# Install QEMU (Linux only)
if test "$(uname)" = "Darwin"; then
    echo "macOS detected, QEMU is not needed."
elif command -v qemu-system-$(uname -m) >/dev/null 2>&1; then
    echo "QEMU is already installed."
else
    echo "Installing QEMU..."
    echo "‼️ You will be prompted for your password to install QEMU using your package manager."
    INSTALL_QEMU_CMD=""

    for pm in "apt-get" "dnf" "pacman" "zypper" "yum" "emerge"; do
        if command -v "$pm" >/dev/null 2>&1; then
            case "$pm" in
                "apt-get")
                    INSTALL_QEMU_CMD="sudo apt-get install -y -qq qemu-system"
                    ;;
                "dnf")
                    INSTALL_QEMU_CMD="sudo dnf install -y -q @virtualization"
                    ;;
                "pacman")
                    INSTALL_QEMU_CMD="sudo pacman -S --noconfirm --noprogressbar qemu"
                    ;;
                "zypper")
                    INSTALL_QEMU_CMD="sudo zypper install -y -qq qemu"
                    ;;
                "yum")
                    INSTALL_QEMU_CMD="sudo yum install -y -q qemu-kvm"
                    ;;
                "emerge")
                    INSTALL_QEMU_CMD="sudo emerge --quiet app-emulation/qemu"
                    ;;
            esac
            break
        fi
    done

    if [ -n "$INSTALL_QEMU_CMD" ]; then
        eval "$INSTALL_QEMU_CMD"
        if [ $? -ne 0 ]; then
            echo "Error: Failed to install QEMU using $pm."
            exit 1
        fi
    else
        echo "Error: No supported package manager found (apt-get, dnf, pacman, zypper, yum, emerge)."
        echo "Please install QEMU manually or refer to https://www.qemu.org/download/ for instructions."
    fi
fi

echo "🚀 Installation complete!"
echo "💡 Open a new terminal window in order to use the 'beeai' command."
