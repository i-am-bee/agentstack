# renovate: datasource=github-releases depName=astral-sh/uv
ARG UV_VERSION=0.10.4
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.13-alpine3.23
ARG RELEASE_VERSION="main"
COPY ./agents/canvas/ /app/agents/canvas
COPY ./apps/agentstack-sdk-py/ /app/apps/agentstack-sdk-py/
WORKDIR /app/agents/canvas
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,from=uv,source=/uv,target=/bin/uv \
    UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy HOME=/tmp uv sync --no-dev
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["/app/agents/canvas/.venv/bin/server"]
