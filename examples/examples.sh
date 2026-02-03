#!/bin/bash
# Manage example agents lifecycle: build, run, and register with agentstack.
#
# This script provides a unified interface for:
# - Building the examples Docker image
# - Running example agents in a Docker container
# - Registering/removing agents with the agentstack platform
#
# Usage:
#   ./examples.sh build   - Build Docker image
#   ./examples.sh run     - Run Docker container (foreground)
#   ./examples.sh add     - Register agents with agentstack
#   ./examples.sh remove  - Remove agents from agentstack
#   ./examples.sh start   - Run Docker (background) and register agents
#   ./examples.sh stop    - Stop the Docker container
#
# Example workflow:
#   ./examples.sh build   # Build the Docker image
#   ./examples.sh start   # Run container and register agents
#   ./examples.sh stop    # Stop the container
#
# Environment variables:
#   EXAMPLES   - Comma-separated list of examples, or "all" (default: all)
#   HOST       - Agent host for registration (default: host.docker.internal)
#   PORT_BASE  - Starting port number (default: 8001)
#   IMAGE      - Docker image name (default: examples)

set -e

HOST="${HOST:-host.docker.internal}"
PORT_BASE="${PORT_BASE:-8001}"
EXAMPLES_INPUT="${EXAMPLES:-all}"
IMAGE="${IMAGE:-examples}"
CONTAINER_NAME="agentstack-examples"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Repository root (Dockerfile must be built from here)
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Build Docker image
do_build() {
	echo "Building Docker image: $IMAGE"
	docker build -t "$IMAGE" -f "$SCRIPT_DIR/Dockerfile" "$REPO_ROOT"
}

# Discover available examples (alphabetical order)
discover_examples() {
	AVAILABLE_EXAMPLES=()
	for dir in "$SCRIPT_DIR"/*/; do
		if [ -f "${dir}pyproject.toml" ]; then
			AVAILABLE_EXAMPLES+=("$(basename "$dir")")
		fi
	done
}

# Build example list based on EXAMPLES input
build_example_list() {
	discover_examples
	if [ "$EXAMPLES_INPUT" = "all" ]; then
		EXAMPLE_LIST=("${AVAILABLE_EXAMPLES[@]}")
	else
		IFS=',' read -ra EXAMPLE_LIST <<<"$EXAMPLES_INPUT"
	fi
}

# Run Docker container
do_run() {
	local detached="${1:-false}"
	build_example_list

	NUM_EXAMPLES=${#EXAMPLE_LIST[@]}
	PORT_END=$((PORT_BASE + NUM_EXAMPLES - 1))
	EXAMPLES_STR=$(IFS=','; echo "${EXAMPLE_LIST[*]}")

	echo "Starting examples: ${EXAMPLES_STR}"
	echo "Ports: ${PORT_BASE}-${PORT_END}"

	local flags=""
	if [ "$detached" = "true" ]; then
		flags="-d"
	fi

	docker run $flags \
		--name "$CONTAINER_NAME" \
		--rm \
		-e EXAMPLES="$EXAMPLES_STR" \
		-e PORT_BASE="$PORT_BASE" \
		-e PLATFORM_URL="http://host.docker.internal:8333" \
		-p "${PORT_BASE}-${PORT_END}:${PORT_BASE}-${PORT_END}" \
		"$IMAGE"
}

# Register agents with agentstack
do_add() {
	build_example_list
	local port=$PORT_BASE

	for example_name in "${EXAMPLE_LIST[@]}"; do
		example_dir="$SCRIPT_DIR/$example_name"

		if [ ! -d "$example_dir" ]; then
			echo "Warning: Example '$example_name' not found, skipping"
			continue
		fi

		# Convert hyphenated name to underscored module name
		module_name="${example_name//-/_}"
		agent_file="${example_dir}/src/${module_name}/agent.py"

		if [ ! -f "$agent_file" ]; then
			echo "Warning: agent.py not found for $example_name, skipping"
			continue
		fi

		# Extract the agent function name (function decorated with @server.agent())
		agent_func=$(grep -A1 '@server.agent()' "$agent_file" | grep 'async def\|def ' | head -1 | sed 's/.*def \([a-zA-Z_][a-zA-Z0-9_]*\).*/\1/')

		if [ -z "$agent_func" ]; then
			echo "Warning: Could not find agent function in $example_name, skipping"
			continue
		fi

		url="http://${HOST}:${port}\#${agent_func}"
		echo "Adding $example_name: $url"
		agentstack add "$url"

		((port++))
	done
}

# Remove agents from agentstack
do_remove() {
	build_example_list

	for example_name in "${EXAMPLE_LIST[@]}"; do
		example_dir="$SCRIPT_DIR/$example_name"

		if [ ! -d "$example_dir" ]; then
			echo "Warning: Example '$example_name' not found, skipping"
			continue
		fi

		# Convert hyphenated name to underscored module name
		module_name="${example_name//-/_}"
		agent_file="${example_dir}/src/${module_name}/agent.py"

		if [ ! -f "$agent_file" ]; then
			echo "Warning: agent.py not found for $example_name, skipping"
			continue
		fi

		# Extract the agent function name (function decorated with @server.agent())
		agent_func=$(grep -A1 '@server.agent()' "$agent_file" | grep 'async def\|def ' | head -1 | sed 's/.*def \([a-zA-Z_][a-zA-Z0-9_]*\).*/\1/')

		if [ -z "$agent_func" ]; then
			echo "Warning: Could not find agent function in $example_name, skipping"
			continue
		fi

		echo "Removing $example_name: $agent_func"
		agentstack remove "$agent_func"
	done
}

# Stop Docker container
do_stop() {
	echo "Stopping $CONTAINER_NAME..."
	docker stop "$CONTAINER_NAME" 2>/dev/null || echo "Container not running"
}

# Wait for container to be ready
wait_for_ready() {
	build_example_list
	local port=$PORT_BASE
	local max_attempts=30

	echo "Waiting for examples to be ready..."
	for example_name in "${EXAMPLE_LIST[@]}"; do
		for ((i=1; i<=max_attempts; i++)); do
			if curl -s "http://localhost:${port}/" >/dev/null 2>&1; then
				echo "  $example_name (port $port): ready"
				break
			fi
			if [ $i -eq $max_attempts ]; then
				echo "  $example_name (port $port): timeout waiting for ready"
			fi
			sleep 1
		done
		((port++))
	done
}

# Main
case "${1:-}" in
	build)
		do_build
		;;
	run)
		do_run false
		;;
	add)
		do_add
		;;
	remove)
		do_remove
		;;
	start)
		do_run true
		wait_for_ready
		do_add
		;;
	stop)
		do_stop
		;;
	*)
		echo "Usage: $0 {build|run|add|remove|start|stop}"
		echo ""
		echo "Commands:"
		echo "  build   - Build Docker image"
		echo "  run     - Run Docker container (foreground)"
		echo "  add     - Register agents with agentstack"
		echo "  remove  - Remove agents from agentstack"
		echo "  start   - Run Docker (background) and register agents"
		echo "  stop    - Stop the Docker container"
		exit 1
		;;
esac
