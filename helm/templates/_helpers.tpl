{{/*
Expand the name of the chart.
*/}}
{{- define "beeai-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "beeai-platform.fullname" -}}
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
{{- define "beeai-platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "beeai-platform.labels" -}}
helm.sh/chart: {{ include "beeai-platform.chart" . }}
{{ include "beeai-platform.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "beeai-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "beeai-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "beeai-platform.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "beeai-platform.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
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
{{- define "beeai.postgresql.fullname" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "postgresql" "chartValues" .Values.postgresql "context" $) -}}
{{- end -}}
{{/*
Return the PostgreSQL Hostname
*/}}
{{- define "beeai.databaseHost" -}}
{{- if .Values.postgresql.enabled }}
    {{- if eq .Values.postgresql.architecture "replication" }}
        {{- printf "%s-%s" (include "beeai.postgresql.fullname" .) "primary" | trunc 63 | trimSuffix "-" -}}
    {{- else -}}
        {{- print (include "beeai.postgresql.fullname" .) -}}
    {{- end -}}
{{- else -}}
    {{- print .Values.externalDatabase.host -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Port
*/}}
{{- define "beeai.databasePort" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.primary.service.ports.postgresql -}}
{{- else -}}
    {{- printf "%d" (.Values.externalDatabase.port | int ) -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Database Name
*/}}
{{- define "beeai.databaseName" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.database -}}
{{- else -}}
    {{- print .Values.externalDatabase.database -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL User
*/}}
{{- define "beeai.databaseUser" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.username -}}
{{- else -}}
    {{- print .Values.externalDatabase.user -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Admin Password
*/}}
{{- define "beeai.databaseAdminUser" -}}
{{- if .Values.postgresql.enabled }}
    {{- printf "postgres" -}}
{{- else -}}
    {{- print .Values.externalDatabase.adminUser -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Password
*/}}
{{- define "beeai.databasePassword" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.password -}}
{{- else -}}
    {{- print .Values.externalDatabase.password -}}
{{- end -}}
{{- end -}}

{{/*
Return the PostgreSQL Admin Password
*/}}
{{- define "beeai.databaseAdminPassword" -}}
{{- if .Values.postgresql.enabled }}
    {{- print .Values.postgresql.auth.postgresPassword -}}
{{- else -}}
    {{- print .Values.externalDatabase.adminPassword -}}
{{- end -}}
{{- end -}}


{{/*
Return the PostgreSQL Secret Name
*/}}
{{- define "beeai.databaseSecretName" -}}
{{- if .Values.postgresql.enabled }}
    {{- if .Values.postgresql.auth.existingSecret -}}
    {{- print .Values.postgresql.auth.existingSecret -}}
    {{- else -}}
    {{- print "beeai-platform-secret" -}}
    {{- end -}}
{{- else if .Values.externalDatabase.existingSecret -}}
    {{- print .Values.externalDatabase.existingSecret -}}
{{- else -}}
    {{- print "beeai-platform-secret" -}}
{{- end -}}
{{- end -}}


{{/*
*** S3 CONFIGURATION ***
(bitnami-style helpers: https://github.com/bitnami/charts/blob/main/bitnami/airflow/templates/_helpers.tpl)
*/}}

{{/*
Return the S3 backend host
*/}}
{{- define "beeai.s3.host" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- printf "seaweedfs-all-in-one" -}}
    {{- else -}}
        {{- print .Values.externalS3.host -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 bucket
*/}}
{{- define "beeai.s3.bucket" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- print .Values.seaweedfs.bucket -}}
    {{- else -}}
        {{- print .Values.externalS3.bucket -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 protocol
*/}}
{{- define "beeai.s3.protocol" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- ternary "https" "http" .Values.seaweedfs.global.enableSecurity -}}
    {{- else -}}
        {{- print .Values.externalS3.protocol -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 region
*/}}
{{- define "beeai.s3.region" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- print "us-east-1"  -}}
    {{- else -}}
        {{- print .Values.externalS3.region -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 port
*/}}
{{- define "beeai.s3.port" -}}
{{- ternary .Values.seaweedfs.s3.port .Values.externalS3.port .Values.seaweedfs.enabled -}}
{{- end -}}

{{/*
Return the S3 endpoint
*/}}
{{- define "beeai.s3.endpoint" -}}
{{- $port := include "beeai.s3.port" . | int -}}
{{- $printedPort := "" -}}
{{- if and (ne $port 80) (ne $port 443) -}}
    {{- $printedPort = printf ":%d" $port -}}
{{- end -}}
{{- printf "%s://%s%s" (include "beeai.s3.protocol" .) (include "beeai.s3.host" .) $printedPort -}}
{{- end -}}

{{/*
Return the S3 credentials secret name
*/}}
{{- define "beeai.s3.secretName" -}}
{{- if .Values.seaweedfs.enabled -}}
    {{- if .Values.seaweedfs.auth.existingSecret -}}
    {{- print .Values.seaweedfs.auth.existingSecret -}}
    {{- else -}}
    {{- print "beeai-platform-secret" -}}
    {{- end -}}
{{- else if .Values.externalS3.existingSecret -}}
    {{- print .Values.externalS3.existingSecret -}}
{{- else -}}
    {{- print "beeai-platform-secret" -}}
{{- end -}}
{{- end -}}

{{/*
Return the S3 access key id inside the secret
*/}}
{{- define "beeai.s3.accessKeyID" -}}
    {{- if .Values.seaweedfs.enabled -}}
        {{- print .Values.seaweedfs.auth.admin.accessKeyID -}}
    {{- else -}}
        {{- print .Values.externalS3.accessKeyID -}}
    {{- end -}}
{{- end -}}

{{/*
Return the S3 secret access key inside the secret
*/}}
{{- define "beeai.s3.accessKeySecret" -}}
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
