FROM python:3.13-slim-bookworm AS builder
RUN apt-get update && apt-get install -y build-essential
COPY ./agents/chat/ /app/agents/chat
COPY ./apps/agentstack-sdk-py/ /app/apps/agentstack-sdk-py/
WORKDIR /app/agents/chat
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    UV_COMPILE_BYTECODE=1 HOME=/tmp uv sync

FROM python:3.13-slim-bookworm
ARG RELEASE_VERSION="main"
COPY --from=builder /app /app
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["/app/agents/chat/.venv/bin/server"]
