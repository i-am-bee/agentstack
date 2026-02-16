{{/*
Validation helpers for Agent Stack Helm chart.
These validators ensure configuration consistency and prevent common deployment issues.
*/}}

{{/*
Run all validators. Include this in any template to trigger validation.
*/}}
{{- define "agentstack.validateAll" -}}
{{- include "agentstack.validate.encryptionKey" . -}}
{{- include "agentstack.validate.authConfig" . -}}
{{- include "agentstack.validate.redisForReplicas" . -}}
{{- end -}}

{{/*
Validate that encryptionKey is provided.
*/}}
{{- define "agentstack.validate.encryptionKey" -}}
{{- if empty .Values.encryptionKey -}}
{{- fail `
ERROR: .Values.encryptionKey is missing.

Please generate one using:
  python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
` -}}
{{- end -}}
{{- end -}}

{{/*
Validate authentication configuration.
*/}}
{{- define "agentstack.validate.authConfig" -}}
{{- if .Values.auth.enabled -}}
  {{- if and (empty .Values.auth.jwtPrivateKey) (not (empty .Values.auth.jwtPublicKey)) -}}
  {{- fail `
ERROR: .Values.auth.jwtPrivateKey is missing but .Values.auth.jwtPublicKey is provided.

Please provide both keys or neither (to auto-generate them).
` -}}
  {{- end -}}
  {{- if and (not (empty .Values.auth.jwtPrivateKey)) (empty .Values.auth.jwtPublicKey) -}}
  {{- fail `
ERROR: .Values.auth.jwtPublicKey is missing but .Values.auth.jwtPrivateKey is provided.

Please provide both keys or neither (to auto-generate them).
` -}}
  {{- end -}}
  {{- if and (not .Values.keycloak.enabled) (empty .Values.externalOidcProvider.issuerUrl) -}}
  {{- fail `
ERROR: Authentication is enabled (auth.enabled=true) but no provider is configured.

You must enable either Keycloak or provide an external OIDC provider:
  1. Enable Keycloak (default):
     keycloak:
       enabled: true

  2. Configure external OIDC provider:
     keycloak:
       enabled: false
     externalOidcProvider:
       issuerUrl: "https://your-oidc-provider.com"
` -}}
  {{- end -}}
{{- end -}}
{{- end -}}

{{/*
Validate that Redis is enabled when running multiple replicas.
Redis is required for distributed rate limiting and caching to work correctly.
*/}}
{{- define "agentstack.validate.redisForReplicas" -}}
{{- if and (gt (int .Values.replicaCount) 1) (ne (include "agentstack.redis.enabled" .) "true") -}}
{{- fail `
ERROR: Redis is required when running multiple replicas (replicaCount > 1).

Redis is needed for distributed rate limiting and caching to work correctly
across all instances. Without Redis, each replica maintains its own counters,
allowing users to exceed limits by distributing requests across replicas.

To fix this, enable Redis by setting one of:
  - redis.enabled=true (use built-in Redis)
  - externalRedis.host=<your-redis-host> (use external Redis)

Alternatively, set replicaCount=1 if you don't need multiple replicas.
` -}}
{{- end -}}
{{- end -}}
