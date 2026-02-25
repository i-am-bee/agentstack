# renovate: datasource=github-releases depName=astral-sh/uv
ARG UV_VERSION=0.10.6@sha256:2f2ccd27bbf953ec7a9e3153a4563705e41c852a5e1912b438fc44d88d6cb52c
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.14-alpine3.23
ARG RELEASE_VERSION="main"
COPY ./agents/form/ /app/agents/form
COPY ./apps/agentstack-sdk-py/ /app/apps/agentstack-sdk-py/
WORKDIR /app/agents/form
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,from=uv,source=/uv,target=/bin/uv \
    UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy HOME=/tmp uv sync --no-dev
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["/app/agents/form/.venv/bin/server"]
