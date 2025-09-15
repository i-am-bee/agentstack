FROM python:3.13-slim-bookworm AS builder
RUN apt-get update && apt-get install -y build-essential
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /bin/
WORKDIR /agents/official/beeai-framework/rag
COPY ./agents/official/beeai-framework/rag/ ./
COPY ./apps/beeai-sdk/ /apps/beeai-sdk/
RUN uv sync --no-cache --link-mode copy

FROM python:3.13-slim-bookworm
ARG RELEASE_VERSION="main"
COPY --from=builder /agents/ /agents/
COPY --from=builder /apps/ /apps/
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["/agents/official/beeai-framework/rag/.venv/bin/server"]
