# renovate: datasource=github-releases depName=astral-sh/uv
ARG UV_VERSION=0.10.6@sha256:2f2ccd27bbf953ec7a9e3153a4563705e41c852a5e1912b438fc44d88d6cb52c
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.14-alpine3.23@sha256:faee120f7885a06fcc9677922331391fa690d911c020abb9e8025ff3d908e510
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HOME="/tmp" \
    AGENT_REGISTRY__LOCATIONS__FILE="file:///app/registry.yaml"
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,source=dist/requirements.txt,target=/requirements.txt \
    --mount=type=bind,from=uv,source=/uv,target=/bin/uv \
    uv pip install --system -r /requirements.txt
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,source=dist,target=/dist \
    --mount=type=bind,from=uv,source=/uv,target=/bin/uv \
    uv pip install --system /dist/*.tar.gz
CMD ["agentstack-server"]
