FROM python:3.13-alpine3.21 AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.9 /uv /bin/
COPY pyproject.toml dist/requirements.txt ./
RUN uv pip install --system -r requirements.txt
COPY dist/*.tar.gz ./
RUN uv pip install --system ./*.tar.gz

FROM python:3.13-alpine3.21
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/beeai-server /usr/local/bin/beeai-server
COPY --from=builder /usr/local/bin/migrate /usr/local/bin/migrate
COPY --from=builder /usr/local/bin/create-buckets /usr/local/bin/create-buckets
COPY --from=builder /usr/local/bin/create-vector-extension /usr/local/bin/create-vector-extension
RUN chmod og+rx /root
ENV PATH="/app/.venv/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    HOME="/tmp" \
    AGENT_REGISTRY__LOCATIONS__FILE="file:///app/registry.yaml"
CMD ["beeai-server"]
