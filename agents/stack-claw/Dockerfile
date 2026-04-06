# renovate: datasource=github-releases depName=astral-sh/uv
ARG UV_VERSION=0.10.9
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.14-alpine3.23@sha256:faee120f7885a06fcc9677922331391fa690d911c020abb9e8025ff3d908e510
ARG RELEASE_VERSION="main"
RUN apk add --no-cache nodejs npm && npm install -g @mariozechner/pi-coding-agent
COPY ./agents/stack-claw/ /app/agents/stack-claw
COPY ./apps/agentstack-sdk-py/ /app/apps/agentstack-sdk-py/
WORKDIR /app/agents/stack-claw
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,from=uv,source=/uv,target=/bin/uv \
    UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy HOME=/tmp uv sync --no-dev
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["/app/agents/stack-claw/.venv/bin/server"]
