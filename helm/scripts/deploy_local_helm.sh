#!/bin/bash

values="
image:
  repository: ghcr.io/i-am-bee/beeai-platform/beeai-server
  tag: local
unmanagedProviderVariables:
  LLM_API_BASE: http://beeai-platform-svc/api/v1/llm
  LLM_API_KEY: dummy
  LLM_MODEL: dummy
encryptionKey: Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=
externalRegistries:
  public_github: https://github.com/i-am-bee/beeai-platform@release-v0.1.3#path=agent-registry.yaml
auth:
  enabled: false
"

helm upgrade --install \
  -f ./variables.ollama.yaml \
  -f <(echo "$values") \
  -n beeai-helm-local \
  --create-namespace \
  my-release \
  beeai-platform
