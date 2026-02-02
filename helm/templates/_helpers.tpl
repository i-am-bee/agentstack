{{/*
Expand the name of the chart.
*/}}
{{- define "agentstack.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "agentstack.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/* Return a safe agent name based on everything after the first "/" */}}
{{- define "agent.fullname" -}}
{{- $root  := .root }}
{{- $image := .image }}

{{- printf "agent-%s" ($image | sha256sum) | trunc 32 | trimSuffix "-" -}}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "agentstack.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Common labels
*/}}
{{- define "agentstack.labels" -}}
helm.sh/chart: {{ include "agentstack.chart" . }}
{{ include "agentstack.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "agentstack.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agentstack.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "agentstack.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "agentstack.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Keycloak Database Environment Variables
*/}}
{{- define "agentstack.keycloak.dbEnvVars" -}}
{{- if not .Values.keycloak.persistence.useDedicatedDatabase }}
# SHARED DATABASE
- name: KC_DB
  value: postgres
- name: KC_DB_SCHEMA
  value: keycloak
- name: 'KC_DB_URL_HOST'
  value: {{ include "agentstack.databaseHost" . | quote }}
- name: 'KC_DB_URL_PORT'
  value: {{ include "agentstack.databasePort" . | quote }}
- name: 'KC_DB_URL_DATABASE'
  value: {{ include "agentstack.databaseName" . | quote }}
- name: 'KC_DB_USERNAME'
  value: {{ include "agentstack.databaseUser" . | quote }}
- name: 'KC_DB_PASSWORD'
  valueFrom:
    secretKeyRef:
      name: keycloak-secret
      key: db-password
{{- else }}
# DEDICATED DATABASE
- name: KC_DB
  value: postgres
- name: KC_DB_SCHEMA
  value: {{ .Values.keycloak.persistence.dedicatedDatabaseConfig.schema | default "keycloak" | quote }}
- name: 'KC_DB_URL_HOST'
  value: {{ .Values.keycloak.persistence.dedicatedDatabaseConfig.host | quote }}
- name: 'KC_DB_URL_PORT'
  value: {{ .Values.keycloak.persistence.dedicatedDatabaseConfig.port | quote }}
- name: 'KC_DB_URL_DATABASE'
  value: {{ .Values.keycloak.persistence.dedicatedDatabaseConfig.database | quote }}
- name: 'KC_DB_USERNAME'
  value: {{ .Values.keycloak.persistence.dedicatedDatabaseConfig.user | quote }}
- name: 'KC_DB_PASSWORD'
  valueFrom:
    secretKeyRef:
      name: keycloak-secret
      key: db-password
{{- if .Values.keycloak.persistence.dedicatedDatabaseConfig.ssl }}
- name: PGSSLMODE
  value: "require"
- name: KC_DB_URL_PROPERTIES
  value: "?sslmode=require"
{{- end }}
{{- end }}
{{- end }}

{{/*
*** DATABASE CONFIGURATION ***
(bitnami-style helpers: https://github.com/bitnami/charts/blob/main/bitnami/airflow/templates/_helpers.tpl)
*/}}

{{/*
Create a default fully qualified postgresql name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "agentstack.postgresql.fullname" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "postgresql" "chartValues" .Values.postgresql "context" $) -}}
{{- end -}}
{{/*
Return the PostgreSQL Hostname
*/}}
{{- define "agentstack.databaseHost" -}}
{{- if .Values.postgresql.enabled }}
    {{- if eq .Values.postgresql.architecture "replication" }}
        {{- printf "%s-%s" (include "agentstack.postgresql.fullname" .) "primary" | trunc 63 | trimSuffix "-" -}}
    {{- else -}}
        {{- print (include "agentstack.postgresql.fullname" .) -}}
    {{- end -}}
{{- else -}}
    {{- print .Values.externalDatabase.host -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Port
*/}}
{{- define "agentstack.databasePort" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.primary.service.ports.postgresql -}}
{{- else -}}
    {{- printf "%d" (.Values.externalDatabase.port | int ) -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Database Name
*/}}
{{- define "agentstack.databaseName" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.database -}}
{{- else -}}
    {{- print .Values.externalDatabase.database -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL User
*/}}
{{- define "agentstack.databaseUser" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.username -}}
{{- else -}}
    {{- print .Values.externalDatabase.user -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Admin Password
*/}}
{{- define "agentstack.databaseAdminUser" -}}
{{- if .Values.postgresql.enabled }}
    {{- printf "postgres" -}}
{{- else -}}
    {{- print .Values.externalDatabase.adminUser -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Password
*/}}
{{- define "agentstack.databasePassword" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.password -}}
{{- else -}}
    {{- print .Values.externalDatabase.password -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Admin Password
*/}}
{{- define "agentstack.databaseAdminPassword" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.postgresPassword -}}
{{- else -}}
    {{- print .Values.externalDatabase.adminPassword -}}
{{- end -}}
{{- end -}}


{{/*
Return the PostgreSQL Secret Name
*/}}
{{- define "agentstack.databaseSecretName" -}}
{{- if .Values.postgresql.enabled }}
    {{- if .Values.postgresql.auth.existingSecret -}}
    {{- print .Values.postgresql.auth.existingSecret -}}
    {{- else -}}
    {{- print "agentstack-secret" -}}
    {{- end -}}
{{- else if .Values.externalDatabase.existingSecret -}}
    {{- print .Values.externalDatabase.existingSecret -}}
{{- else -}}
    {{- print "agentstack-secret" -}}
{{- end -}}
{{- end -}}

{{/*
Return if SSL is enabled
*/}}
{{- define "agentstack.databaseSslEnabled" -}}
{{- if and (not .Values.postgresql.enabled) .Values.externalDatabase.ssl -}}
true
{{- end -}}
{{- end -}}


{{/*
*** S3 CONFIGURATION ***
(bitnami-style helpers: https://github.com/bitnami/charts/blob/main/bitnami/airflow/templates/_helpers.tpl)
*/}}

{{/*
Return the S3 backend host
*/}}
{{- define "agentstack.s3.host" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- printf "seaweedfs-all-in-one" -}}
    {{- else -}}
        {{- print .Values.externalS3.host -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 bucket
*/}}
{{- define "agentstack.s3.bucket" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- print .Values.seaweedfs.bucket -}}
    {{- else -}}
        {{- print .Values.externalS3.bucket -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 protocol
*/}}
{{- define "agentstack.s3.protocol" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- ternary "https" "http" .Values.seaweedfs.global.enableSecurity -}}
    {{- else -}}
        {{- print .Values.externalS3.protocol -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 region
*/}}
{{- define "agentstack.s3.region" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- print "us-east-1"  -}}
    {{- else -}}
        {{- print .Values.externalS3.region -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 port
*/}}
{{- define "agentstack.s3.port" -}}
{{- ternary .Values.seaweedfs.s3.port .Values.externalS3.port .Values.seaweedfs.enabled -}}
{{- end -}}

{{/*
Return the S3 endpoint
*/}}
{{- define "agentstack.s3.endpoint" -}}
{{- $port := include "agentstack.s3.port" . | int -}}
{{- $printedPort := "" -}}
{{- if and (ne $port 80) (ne $port 443) -}}
    {{- $printedPort = printf ":%d" $port -}}
{{- end -}}
{{- printf "%s://%s%s" (include "agentstack.s3.protocol" .) (include "agentstack.s3.host" .) $printedPort -}}
{{- end -}}

{{/*
Return the S3 credentials secret name
*/}}
{{- define "agentstack.s3.secretName" -}}
{{- if .Values.seaweedfs.enabled -}}
    {{- if .Values.seaweedfs.auth.existingSecret -}}
    {{- print .Values.seaweedfs.auth.existingSecret -}}
    {{- else -}}
    {{- print "agentstack-secret" -}}
    {{- end -}}
{{- else if .Values.externalS3.existingSecret -}}
    {{- print .Values.externalS3.existingSecret -}}
{{- else -}}
    {{- print "agentstack-secret" -}}
{{- end -}}
{{- end -}}

{{/*
Return the S3 access key id inside the secret
*/}}
{{- define "agentstack.s3.accessKeyID" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- print .Values.seaweedfs.auth.admin.accessKeyID -}}
    {{- else -}}
        {{- print .Values.externalS3.accessKeyID -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 secret access key inside the secret
*/}}
{{- define "agentstack.s3.accessKeySecret" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- print .Values.seaweedfs.auth.admin.accessKeySecret  -}}
    {{- else -}}
        {{- print .Values.externalS3.accessKeySecret -}}
    {{- end -}}
{{- end -}}



{{/*
PATCH phoenix validatePersistence helper because the chart/image is broken and does not work with sqlalchemy
We need to set database.url otherwise migrations fail
*/}}
{{- define "phoenix.validatePersistence" -}}
    {{- $persistenceEnabled := .Values.persistence.enabled | toString | eq "true" }}
    {{- $postgresqlEnabled := .Values.postgresql.enabled | toString | eq "true" }}
    {{- $databaseUrlConfigured := and .Values.database.url (ne .Values.database.url "") }}
    {{- $isMemoryDatabase := .Values.persistence.inMemory | toString | eq "true" }}
    {{- if and $isMemoryDatabase $postgresqlEnabled }}
        {{- fail "ERROR: In-memory database configuration conflict!\n\nWhen using SQLite In-memory (database.url=\"sqlite:///:memory:\"), PostgreSQL must be disabled.\n\nTo fix this:\n  - Set database.url=\"sqlite:///:memory:\"\n  - Set postgresql.enabled=false\n\nNote: In-memory mode is for demos/testing only. All data will be lost when the pod restarts." }}
    {{- end }}
    {{- if and $persistenceEnabled $postgresqlEnabled (not $isMemoryDatabase) }}
        {{- fail "ERROR: Invalid persistence configuration detected!\n\nYou cannot enable both 'persistence.enabled=true' and 'postgresql.enabled=true' simultaneously.\n\nThese options are mutually exclusive. Please choose ONE of the following:\n\n  1. SQLite with persistent storage:\n     - Set persistence.enabled=true\n     - Set postgresql.enabled=false\n     - Leave database.url empty\n\n  2. Built-in PostgreSQL:\n     - Set persistence.enabled=false\n     - Set postgresql.enabled=true\n     - Leave database.url empty\n\n  3. External database:\n     - Set persistence.enabled=false\n     - Set postgresql.enabled=false\n     - Configure database.url with your external database connection string\n\nFor more information, see the persistence configuration comments in values.yaml" }}
    {{- end }}
    {{- if and $persistenceEnabled $databaseUrlConfigured (not $isMemoryDatabase) }}
        {{/* We need to disable this check:*/}}
        {{/*  {{- fail "ERROR: Invalid SQLite configuration detected!\n\nWhen using SQLite with persistent storage (persistence.enabled=true), the 'database.url' must be empty.\n\nSQLite will automatically use the persistent volume at the working directory.\n\nTo fix this:\n  - Set persistence.enabled=true\n  - Set postgresql.enabled=false\n  - Set database.url to empty string\n\nIf you want to use an external database instead:\n  - Set persistence.enabled=false\n  - Set postgresql.enabled=false\n  - Configure database.url with your external database connection string" }}*/}}
    {{- end }}
    {{- if and $databaseUrlConfigured $postgresqlEnabled (not $isMemoryDatabase) }}
        {{- fail "ERROR: Conflicting database configuration detected!\n\nYou cannot specify both 'database.url' and enable the built-in PostgreSQL (postgresql.enabled=true).\n\nTo fix this, choose ONE option:\n\n  1. Use external database:\n     - Set postgresql.enabled=false\n     - Keep database.url configured with your external database\n\n  2. Use built-in PostgreSQL:\n     - Set postgresql.enabled=true\n     - Set database.url to empty string\n\nThe database.url setting overrides PostgreSQL settings, so having both enabled creates ambiguity." }}
    {{- end }}
{{- end }}

{{/*
Generate imagePullSecrets including optional internal registry secret
*/}}
{{- define "agentstack.imagePullSecrets" -}}
{{- $secrets := list -}}
{{- range .Values.imagePullSecrets -}}
  {{- $secrets = append $secrets . -}}
{{- end -}}
{{- if .Values.localDockerRegistry.enabled -}}
  {{- $internalSecret := dict "name" "agentstack-registry-secret" -}}
  {{- $secrets = append $secrets $internalSecret -}}
{{- end -}}
{{- if $secrets -}}
imagePullSecrets:
{{- range $secrets }}
  - name: {{ .name }}
{{- end -}}
{{- end -}}
{{- end }}


{{/*
Generate environment variables for registry docker configs
*/}}
{{- define "agentstack.registryEnvVars" -}}
{{- $secrets := list -}}
{{- range .Values.imagePullSecrets -}}
  {{- $secrets = append $secrets . -}}
{{- end -}}
{{- if .Values.localDockerRegistry.enabled -}}
  {{- $internalSecret := dict "name" "agentstack-registry-secret" -}}
  {{- $secrets = append $secrets $internalSecret -}}
{{- end -}}
{{- range $idx, $secret := $secrets }}
- name: OCI_REGISTRY_DOCKER_CONFIG_JSON__{{ $idx }}
  valueFrom:
    secretKeyRef:
      name: {{ $secret.name }}
      key: ".dockerconfigjson"
{{- end }}
{{- end }}

{{/*
*** REDIS CONFIGURATION ***
*/}}

{{/*
Create a default fully qualified redis name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "agentstack.redis.fullname" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "redis" "chartValues" .Values.redis "context" $) -}}
{{- end -}}

{{/*
Return the Redis Hostname
*/}}
{{- define "agentstack.redis.host" -}}
{{- if .Values.redis.enabled }}
    {{- print (include "agentstack.redis.fullname" .) -}}
{{- else -}}
    {{- print .Values.externalRedis.host -}}
{{- end -}}
{{- end -}}

{{/*
Return the Redis Port
*/}}
{{- define "agentstack.redis.port" -}}
{{- if .Values.redis.enabled }}
    {{- print "6379" -}}
{{- else -}}
    {{- printf "%d" (.Values.externalRedis.port | int ) -}}
{{- end -}}
{{- end -}}

{{/*
Return the Redis Password
*/}}
{{- define "agentstack.redis.password" -}}
{{- if .Values.redis.enabled }}
    {{- print .Values.redis.auth.password -}}
{{- else -}}
    {{- print .Values.externalRedis.password -}}
{{- end -}}
{{- end -}}

{{/*
Return the Redis Secret Name
*/}}
{{- define "agentstack.redis.secretName" -}}
{{- if .Values.redis.enabled }}
    {{- if .Values.redis.auth.existingSecret -}}
    {{- print .Values.redis.auth.existingSecret -}}
    {{- else -}}
    {{- printf "%s" (include "agentstack.redis.fullname" .) -}}
    {{- end -}}
{{- else if .Values.externalRedis.existingSecret -}}
    {{- print .Values.externalRedis.existingSecret -}}
{{- else -}}
    {{- print "agentstack-secret" -}}
{{- end -}}
{{- end -}}

{{/*
Return the Redis Secret Password Key
*/}}
{{- define "agentstack.redis.secretPasswordKey" -}}
{{- if .Values.redis.enabled }}
    {{- if .Values.redis.auth.existingSecretPasswordKey -}}
    {{- print .Values.redis.auth.existingSecretPasswordKey -}}
    {{- else -}}
    {{- print "redis-password" -}}
    {{- end -}}
{{- else if .Values.externalRedis.existingSecretPasswordKey -}}
    {{- print .Values.externalRedis.existingSecretPasswordKey -}}
{{- end -}}
{{- end -}}

{{/*
Return if Redis is enabled
*/}}
{{- define "agentstack.redis.enabled" -}}
{{- if or .Values.redis.enabled .Values.externalRedis.host -}}
true
{{- else -}}
false
{{- end -}}
{{- end -}}

{{- define "agentstack.phoenix.fullname" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "phoenix" "chartValues" .Values.phoenix "context" $) -}}
{{- end -}}

{{/*
Return if Redis is enabled
*/}}
{{- define "agentstack.phoenix.enabled" -}}
{{- or .Values.phoenix.enabled .Values.externalPhoenix.url -}}
{{- end -}}

{{/*
Return the Phoenix URL
*/}}
{{- define "agentstack.phoenix.url" -}}
{{- if .Values.phoenix.enabled }}
    {{- printf "http://%s-svc:6006" (include "agentstack.phoenix.fullname" .) -}}
{{- else -}}
    {{- .Values.externalPhoenix.url -}}
{{- end -}}
{{- end -}}

{{/*
Return the Phoenix API KEY
*/}}
{{- define "agentstack.phoenix.apiKey" -}}
{{- if .Values.phoenix.enabled }}
    {{- "" -}}
{{- else -}}
    {{- print .Values.externalPhoenix.apiKey -}}
{{- end -}}
{{- end -}}

{{/*
*** OIDC CONFIGURATION ***
*/}}

{{/*
Return the OIDC Issuer URL
*/}}
{{- define "agentstack.oidc.issuerUrl" -}}
{{- if .Values.keycloak.enabled -}}
    {{- if .Values.keycloak.publicIssuerUrl -}}
        {{- print .Values.keycloak.publicIssuerUrl -}}
    {{- else -}}
        {{- printf "http://keycloak:%d/realms/agentstack" (.Values.keycloak.service.port | int) -}}
    {{- end -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.issuerUrl -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC UI Client ID
*/}}
{{- define "agentstack.oidc.uiClientId" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "agentstack-ui" -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.uiClientId -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC Server Client ID
*/}}
{{- define "agentstack.oidc.serverClientId" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "agentstack-server" -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.serverClientId -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC UI Client Secret Name
*/}}
{{- define "agentstack.oidc.uiClientSecretName" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "agentstack-ui-secret" -}}
{{- else -}}
    {{- if .Values.externalOidcProvider.existingSecret -}}
        {{- print .Values.externalOidcProvider.existingSecret -}}
    {{- else -}}
        {{- print "agentstack-ui-secret" -}}
    {{- end -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC UI Client Secret Key
*/}}
{{- define "agentstack.oidc.uiClientSecretKey" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "agentstackUiClientSecret" -}}
{{- else -}}
    {{- if .Values.externalOidcProvider.existingSecret -}}
        {{- print .Values.externalOidcProvider.uiClientSecretKey -}}
    {{- else -}}
        {{- print "agentstackUiClientSecret" -}}
    {{- end -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC Server Client Secret Name
*/}}
{{- define "agentstack.oidc.serverClientSecretName" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "agentstack-secret" -}}
{{- else -}}
    {{- if .Values.externalOidcProvider.existingSecret -}}
        {{- print .Values.externalOidcProvider.existingSecret -}}
    {{- else -}}
        {{- print "agentstack-secret" -}}
    {{- end -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC Server Client Secret Key
*/}}
{{- define "agentstack.oidc.serverClientSecretKey" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "agentstackServerClientSecret" -}}
{{- else -}}
    {{- if .Values.externalOidcProvider.existingSecret -}}
        {{- print .Values.externalOidcProvider.serverClientSecretKey -}}
    {{- else -}}
        {{- print "agentstackServerClientSecret" -}}
    {{- end -}}
{{- end -}}
{{- end -}}

{{- define "agentstack.oidc.providerName" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "Keycloak" -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.name -}}
{{- end -}}
{{- end -}}

{{- define "agentstack.oidc.providerId" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "keycloak" -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.id -}}
{{- end -}}
{{- end -}}

{{- define "agentstack.oidc.rolesPath" -}}
{{- if .Values.keycloak.enabled -}}
    {{- print "realm_access.roles" -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.rolesPath -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC UI Client Secret Value (Logic extracted)
*/}}
{{- define "agentstack.oidc.uiClientSecretValue" -}}
{{- if .Values.keycloak.enabled -}}
    {{- $uiClientSecret := .Values.keycloak.uiClientSecret -}}
    {{- $secret := (lookup "v1" "Secret" .Release.Namespace "agentstack-ui-secret") -}}
    {{- if and $secret $secret.data (hasKey $secret.data "agentstackUiClientSecret") -}}
        {{- $uiClientSecret = index $secret.data "agentstackUiClientSecret" | b64dec -}}
    {{- end -}}
    {{- if not $uiClientSecret -}}
        {{- $uiClientSecret = randAlphaNum 32 -}}
    {{- end -}}
    {{- print $uiClientSecret -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.uiClientSecret -}}
{{- end -}}
{{- end -}}

{{/*
Return the OIDC Server Client Secret Value (Logic extracted)
*/}}
{{- define "agentstack.oidc.serverClientSecretValue" -}}
{{- if .Values.keycloak.enabled -}}
    {{- $serverClientSecret := .Values.keycloak.serverClientSecret -}}
    {{- $secret := (lookup "v1" "Secret" .Release.Namespace "agentstack-secret") -}}
    {{- if and $secret $secret.data (hasKey $secret.data "agentstackServerClientSecret") -}}
        {{- $serverClientSecret = index $secret.data "agentstackServerClientSecret" | b64dec -}}
    {{- end -}}
    {{- if not $serverClientSecret -}}
        {{- $serverClientSecret = randAlphaNum 32 -}}
    {{- end -}}
    {{- print $serverClientSecret -}}
{{- else -}}
    {{- print .Values.externalOidcProvider.serverClientSecret -}}
{{- end -}}
{{- end -}}