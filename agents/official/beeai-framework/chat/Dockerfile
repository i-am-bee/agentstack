FROM python:3.13-slim-bookworm
ARG RELEASE_VERSION="main"

# TODO: temporary git for beeai-sdk git dependency
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.6.16 /uv /bin/
WORKDIR /app
COPY . .
RUN uv sync --no-cache --locked --link-mode copy
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["uv", "run", "--no-sync", "server"]
