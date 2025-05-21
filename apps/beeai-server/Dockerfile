FROM python:3.11-alpine3.21 AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /bin/
RUN apk add --no-cache gcc musl-dev linux-headers rust cargo
COPY /apps/beeai-server/pyproject.toml .
ENV UV_NO_CACHE=1
RUN uv pip compile pyproject.toml >requirements.txt && \
    uv pip install --system -r requirements.txt && \
    rm requirements.txt pyproject.toml
COPY /apps/beeai-server/dist/*.tar.gz .
RUN uv pip install --system ./*.tar.gz

FROM python:3.11-alpine3.21
WORKDIR /app
RUN apk add --no-cache libgcc
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/beeai-server /usr/local/bin/beeai-server
RUN chmod og+rx /root
ENV PATH="/app/.venv/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    HOME="/tmp" \
    DISABLE_DOCKER=true \
    COLLECTOR_MANAGED=false \
    AGENT_REGISTRY__LOCATION="file:///app/registry.yaml" \
    UV_NO_CACHE=1
CMD ["beeai-server"]
