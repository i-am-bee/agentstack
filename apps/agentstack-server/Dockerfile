FROM python:3.13-alpine3.22 AS builder
ENV UV_COMPILE_BYTECODE=1 \
    HOME="/tmp" \
    AGENT_REGISTRY__LOCATIONS__FILE="file:///app/registry.yaml"
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,source=dist/requirements.txt,target=/requirements.txt \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    uv pip install --system -r /requirements.txt
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,source=dist,target=/dist \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    uv pip install --system /dist/*.tar.gz
CMD ["agentstack-server"]
