FROM python:3.11-alpine3.21 AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /bin/
# tiktoken builds using rust and cargo
RUN apk add --no-cache rust cargo
COPY pyproject.toml .
RUN uv pip compile pyproject.toml >requirements.txt && \
    uv pip install --system -r requirements.txt && \
    rm requirements.txt pyproject.toml
COPY dist/*.tar.gz .
RUN uv pip install --system ./*.tar.gz

FROM python:3.11-alpine3.21
WORKDIR /app
# tiktoken requires libgcc
RUN apk add --no-cache libgcc
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/beeai-server /usr/local/bin/beeai-server
COPY --from=builder /usr/local/bin/migrate /usr/local/bin/migrate
COPY --from=builder /usr/local/bin/create-buckets /usr/local/bin/create-buckets
RUN chmod og+rx /root
ENV PATH="/app/.venv/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    HOME="/tmp" \
    AGENT_REGISTRY__LOCATIONS__FILE="file:///app/registry.yaml"
CMD ["beeai-server"]
