#!/bin/sh
set -eu

# Configurable through env vars:
# BEEAI_VERSION = latest (default, latest stable version) | pre (latest version including prereleases) | <version> (specific version)

# These get updated by `mise release`:
LATEST_STABLE_BEEAI_VERSION=0.3.5
LATEST_BEEAI_VERSION=0.3.5

error() {
    printf "\n💥 \033[31mERROR:\033[0m: BeeAI installation has failed. Please report the above error: https://github.com/i-am-bee/beeai-platform/issues\n" >&2
    exit 1
}

echo "Starting the BeeAI installer..."

# Ensure that we have uv on PATH
export PATH="${XDG_BIN_HOME:+${XDG_BIN_HOME}:}${XDG_DATA_HOME:+$(realpath -m ${XDG_DATA_HOME}/../bin):}${HOME:+${HOME}/.local/bin:}$PATH"

# Always install uv to ensure we have the latest version for consistency
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | UV_PRINT_QUIET=1 sh || error

# Separately uninstall potential old version of beeai-cli to remove envs created with wrong Python versions
# --no-bin to avoid putting it in PATH (not necessary)
uv tool uninstall --quiet beeai-cli >/dev/null 2>&1 || true

# Install a uv-managed Python version (uv should do that automatically but better be explicit)
echo "Installing Python..."
uv python install --quiet --managed-python --no-bin 3.13 || error

# Install beeai-cli using a uv-managed Python version
# We set the versions of beeai-cli and beeai-sdk to error out on platforms incompatible with the latest version
# It also avoids accidentally installing prereleases of dependencies by only allowing explicitly set ones
echo "Installing beeai-cli..."
case "${BEEAI_VERSION:-latest}" in "latest") BEEAI_VERSION=$LATEST_STABLE_BEEAI_VERSION ;; "pre") BEEAI_VERSION=$LATEST_BEEAI_VERSION ;; esac
uv tool install --quiet --managed-python --python=3.13 --refresh --prerelease if-necessary-or-explicit --with "beeai-sdk==$BEEAI_VERSION" "beeai-cli==$BEEAI_VERSION" || error

# Finish set up using CLI (install QEMU on Linux, start platform, set up API keys, run UI, ...)
beeai self install
