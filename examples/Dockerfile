FROM python:3.13-slim
ARG RELEASE_VERSION="main"

# Copy SDK (shared dependency) - path matches pyproject.toml relative reference
COPY ./apps/agentstack-sdk-py/ /app/apps/agentstack-sdk-py/

# Copy all example agents
COPY ./examples/ /app/examples/

# Install each agent's dependencies
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    UV_COMPILE_BYTECODE=1 HOME=/tmp && \
    for example_dir in /app/examples/*/; do \
        if [ -f "${example_dir}pyproject.toml" ]; then \
            cd "$example_dir" && uv sync; \
        fi; \
    done

ENV PRODUCTION_MODE=True \ 
    RELEASE_VERSION=${RELEASE_VERSION}

COPY ./examples/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]