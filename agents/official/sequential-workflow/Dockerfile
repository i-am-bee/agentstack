FROM python:3.13-slim-bookworm
ARG RELEASE_VERSION="main"
COPY --from=ghcr.io/astral-sh/uv:0.6.16 /uv /bin/
WORKDIR /app
WORKDIR /agents/official/sequential-workflow
COPY ./agents/official/sequential-workflow/ ./
COPY ./apps/beeai-sdk/ /apps/beeai-sdk/
RUN uv sync --no-cache --locked --link-mode copy
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["uv", "run", "--no-sync", "server"]
