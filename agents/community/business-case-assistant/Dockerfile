FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.6.16 /uv /bin/

ENV UV_LINK_MODE=copy \
    PRODUCTION_MODE=true

ADD . /app
WORKDIR /app

RUN uv sync --no-cache --locked --link-mode copy

ENV PRODUCTION_MODE=True \
    PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "--no-sync", "server"]