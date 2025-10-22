FROM registry.access.redhat.com/ubi9/python-312
ENV AGENT_REGISTRY__LOCATIONS__FILE="file:///app/registry.yaml"
RUN --mount=type=bind,source=dist/requirements.txt,target=requirements.txt \
    pip install -r requirements.txt
RUN --mount=type=bind,source=dist,target=dist \
    pip install dist/*.tar.gz
CMD ["beeai-server"]
