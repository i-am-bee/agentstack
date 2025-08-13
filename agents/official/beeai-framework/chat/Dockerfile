FROM python:3.13-slim-bookworm
ARG RELEASE_VERSION="main"
COPY --from=ghcr.io/astral-sh/uv:0.8.9 /uv /bin/
WORKDIR /agents/official/beeai-framework/chat
COPY ./agents/official/beeai-framework/chat/ ./
COPY ./apps/beeai-sdk/ /apps/beeai-sdk/
RUN uv sync --no-cache --link-mode copy
ENV PRODUCTION_MODE=True \
    RELEASE_VERSION=${RELEASE_VERSION}
CMD ["uv", "run", "--no-sync", "server"]
