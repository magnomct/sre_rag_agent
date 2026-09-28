{{/*
Common labels for all resources
*/}}
{{- define "sre-rag.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: sre-rag-lab
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
environment: {{ .Values.global.environment }}
team: sre
{{- end }}

{{/*
Selector labels for API
*/}}
{{- define "sre-rag.api.selectorLabels" -}}
app.kubernetes.io/name: sre-rag-api
app.kubernetes.io/component: backend
{{- end }}

{{/*
Selector labels for PostgreSQL
*/}}
{{- define "sre-rag.postgresql.selectorLabels" -}}
app.kubernetes.io/name: postgresql
app.kubernetes.io/component: database
{{- end }}

{{/*
Selector labels for Redis
*/}}
{{- define "sre-rag.redis.selectorLabels" -}}
app.kubernetes.io/name: redis
app.kubernetes.io/component: cache
{{- end }}

{{/*
Full name helper
*/}}
{{- define "sre-rag.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}
