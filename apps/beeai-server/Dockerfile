FROM jdxcode/mise AS build
ENV UV_LINK_MODE copy
ENV UV_COMPILE_BYTECODE 1
WORKDIR /app
COPY . .
# `python.uv_venv_auto` must be `false` to avoid https://github.com/rancher-sandbox/rancher-desktop/issues/8281
RUN --mount=type=cache,target=/mise/downloads \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.local/share/pnpm/store \
    mise trust &&\
    mise settings set --local python.uv_venv_auto false &&\
    mise install &&\
    mise run beeai-server:build

FROM debian:12-slim AS runtime
WORKDIR /app
RUN apt-get update &&\
    apt-get -y --no-install-recommends install pipx &&\
    rm -rf /var/lib/apt/lists/*
COPY --from=build /app/apps/beeai-server/dist/*.tar.gz .
RUN pipx install ./*.tar.gz
RUN chmod og+rx /root
ENV PATH="/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    HOME="/tmp" \
    DISABLE_DOCKER=true \
    COLLECTOR_MANAGED=false \
    AGENT_REGISTRY__LOCATION="file:///app/registry.yaml"
CMD ["beeai-server"]
