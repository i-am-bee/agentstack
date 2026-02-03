#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/.template/example"

usage() {
    echo "Usage: $0 <path> <description>"
    echo ""
    echo "Arguments:"
    echo "  path         Path relative to examples/ (e.g., agent-integration/multi-turn/basic-history)"
    echo "  description  Short description of the example"
    echo ""
    echo "The example name is derived from the last folder in the path."
    echo ""
    echo "Example:"
    echo "  $0 agent-integration/multi-turn/basic-history \"Example demonstrating basic history.\""
    exit 1
}

if [[ $# -ne 2 ]]; then
    usage
fi

path="$1"
description="$2"
target_dir="$SCRIPT_DIR/$path"
name="$(basename "$path")"
snake_name="${name//-/_}"

# Compute relative SDK path based on directory depth
# From examples/<path>/ we need to reach <repo>/apps/agentstack-sdk-py
# That's (number of segments in path + 1) levels up
IFS='/' read -ra segments <<< "$path"
sdk_path=""
for ((i = 0; i <= ${#segments[@]}; i++)); do
    sdk_path="../$sdk_path"
done
sdk_path="${sdk_path}apps/agentstack-sdk-py"

if [[ -e "$target_dir" ]]; then
    echo "Error: $target_dir already exists" >&2
    exit 1
fi

# Create parent directories if needed
mkdir -p "$(dirname "$target_dir")"

# Copy template
cp -r "$TEMPLATE_DIR" "$target_dir"

# Rename sentinel directory
mv "$target_dir/src/example_name" "$target_dir/src/$snake_name"

# Replace placeholders in all files
find "$target_dir" -type f | while read -r file; do
    sed -i.bak \
        -e "s|%{EXAMPLE_NAME}|${name}|g" \
        -e "s|%{EXAMPLE_DESCRIPTION}|${description}|g" \
        -e "s|%{EXAMPLE_NAME_SNAKECASE}|${snake_name}|g" \
        -e "s|%{SDK_PATH}|${sdk_path}|g" \
        -e "s|example_name|${snake_name}|g" \
        "$file"
    rm -f "$file.bak"
done

echo "Created example '$name' at $target_dir"
