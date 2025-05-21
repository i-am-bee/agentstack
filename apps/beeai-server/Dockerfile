FROM debian:bookworm-slim
# bookworm uses python 3.11
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /bin/
ENV UV_NO_CACHE=1
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 &&\
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY /apps/beeai-server/pyproject.toml .
RUN rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED && \
    uv pip compile pyproject.toml >requirements.txt && \
    uv pip install --system -r requirements.txt && \
    rm requirements.txt pyproject.toml
COPY /apps/beeai-server/dist/*.tar.gz .
RUN rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED && \
    uv pip install --system ./*.tar.gz
RUN chmod og+rx /root
ENV PATH="/app/.venv/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    HOME="/tmp" \
    DISABLE_DOCKER=true \
    COLLECTOR_MANAGED=false \
    AGENT_REGISTRY__LOCATION="file:///app/registry.yaml"
CMD ["beeai-server"]
