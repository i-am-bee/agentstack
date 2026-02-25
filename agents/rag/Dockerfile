# renovate: datasource=github-releases depName=astral-sh/uv
ARG UV_VERSION=0.10.4@sha256:4cac394b6b72846f8a85a7a0e577c6d61d4e17fe2ccee65d9451a8b3c9efb4ac
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.13-alpine3.23
ARG RELEASE_VERSION="main"
COPY ./agents/rag/ /app/agents/rag
COPY ./apps/agentstack-sdk-py/ /app/apps/agentstack-sdk-py/
WORKDIR /app/agents/rag
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,from=uv,source=/uv,target=/bin/uv \
    UV_COMPILE_BYTECODE=1 HOME=/tmp uv sync --no-dev
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["/app/agents/rag/.venv/bin/server"]
