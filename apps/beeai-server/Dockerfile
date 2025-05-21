FROM debian:12-slim
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /bin/
WORKDIR /app
COPY /apps/beeai-server/pyproject.toml .
RUN uv venv && \
    uv pip compile pyproject.toml >requirements.txt && \
    uv pip install -r requirements.txt
COPY /apps/beeai-server/dist/*.tar.gz .
RUN uv pip install ./*.tar.gz
RUN chmod og+rx /root
ENV PATH="/app/.venv/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    HOME="/tmp" \
    DISABLE_DOCKER=true \
    COLLECTOR_MANAGED=false \
    AGENT_REGISTRY__LOCATION="file:///app/registry.yaml"
CMD ["beeai-server"]
