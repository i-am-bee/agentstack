#!/bin/bash
set -e

# EXAMPLES: comma-separated list, e.g. "basic-history", "basic-history,advanced-history", or "all"
EXAMPLES_INPUT="${EXAMPLES:-all}"

# Discover available examples
AVAILABLE_EXAMPLES=()
for dir in /app/examples/*/; do
	if [ -f "${dir}pyproject.toml" ]; then
		example_name=$(basename "$dir")
		AVAILABLE_EXAMPLES+=("$example_name")
	fi
done

if [ "$EXAMPLES_INPUT" = "all" ]; then
	EXAMPLE_LIST=("${AVAILABLE_EXAMPLES[@]}")
else
	IFS=',' read -ra EXAMPLE_LIST <<<"$EXAMPLES_INPUT"
fi

echo "Starting examples: ${EXAMPLE_LIST[*]}"

PIDS=()
PORT_BASE=${PORT_BASE:-8001}

for example in "${EXAMPLE_LIST[@]}"; do
	example_dir="/app/examples/$example"

	if [ ! -d "$example_dir" ]; then
		echo "Warning: Example '$example' not found, skipping"
		continue
	fi

	echo "Starting $example on port $PORT_BASE"
	cd "$example_dir"
	PORT=$PORT_BASE HOST=0.0.0.0 "$example_dir/.venv/bin/server" &
	PIDS+=($!)
	((PORT_BASE++))
done

if [ ${#PIDS[@]} -eq 0 ]; then
	echo "Error: No examples started"
	exit 1
fi

# Handle shutdown gracefully
trap 'kill "${PIDS[@]}" 2>/dev/null' SIGTERM SIGINT

# Wait for all processes
wait
