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

{{- /* Step 1: strip the registry part */}}
{{- $path := regexReplaceAll "^[^/]+/(.+?[:@].*)?$" $image "$1" }}

{{- $shortpath := replace "i-am-bee/beeai-platform/" "" $path }}
{{- $name := replace ":" "-" (replace "/" "-" $shortpath) }}

{{- printf "%s" $name | trunc 63 | trimSuffix "-" -}}
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
