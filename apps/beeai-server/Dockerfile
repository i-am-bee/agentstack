FROM registry.access.redhat.com/ubi9/python-312
ENV UV_COMPILE_BYTECODE=1 \
    AGENT_REGISTRY__LOCATIONS__FILE="file:///app/registry.yaml"
RUN --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001,gid=0,mode=0775 \
    --mount=type=bind,source=dist/requirements.txt,target=/requirements.txt \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    uv pip install --python=/opt/app-root/bin/python -r /requirements.txt
RUN --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001,gid=0,mode=0775 \
    --mount=type=bind,source=dist,target=/dist \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.9.5,source=/uv,target=/bin/uv \
    uv pip install --python=/opt/app-root/bin/python /dist/*.tar.gz
CMD ["/opt/app-root/bin/beeai-server"]
