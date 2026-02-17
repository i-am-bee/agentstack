FROM python:3.13-slim
ARG RELEASE_VERSION="main"
COPY ./agents/langgraph-reflection/ /app/agents/langgraph-reflection
COPY ./apps/agentstack-sdk-py/ /app/apps/agentstack-sdk-py/
WORKDIR /app/agents/langgraph-reflection
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    UV_COMPILE_BYTECODE=1 HOME=/tmp uv sync --no-dev
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["/app/agents/langgraph-reflection/.venv/bin/server"]
