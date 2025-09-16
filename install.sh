#!/bin/sh
set -eu

# Configurable through env vars:
# BEEAI_VERSION = latest (default, installs the latest version) | pre (installs latest prerelease using --pre) | <version> (installs with "beeai-cli==<version>")

echo "Starting the BeeAI installer..."

new_path="${XDG_BIN_HOME:+${XDG_BIN_HOME}:}${XDG_DATA_HOME:+$(realpath -m ${XDG_DATA_HOME}/../bin):}${HOME:+${HOME}/.local/bin:}$PATH"

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | UV_PRINT_QUIET=1 sh
fi

echo "Installing beeai-cli..."
case "${BEEAI_VERSION:-latest}" in
"latest") PATH="$new_path" uv tool install --refresh --quiet --force beeai-cli ;;
"pre")    PATH="$new_path" uv tool install --refresh --quiet --force --pre beeai-cli ;;
*)        PATH="$new_path" uv tool install --refresh --quiet --force "beeai-cli==$BEEAI_VERSION" ;;
esac
PATH="$new_path" beeai self install
