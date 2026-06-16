{{/*
Expand the chart name.
*/}}
{{- define "spliteasy.name" -}}
{{- .Chart.Name }}
{{- end }}

{{/*
Create a fully qualified release name (max 63 chars).
*/}}
{{- define "spliteasy.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Backend service/deployment name.
*/}}
{{- define "spliteasy.backendName" -}}
{{- printf "%s-backend" (include "spliteasy.fullname" .) }}
{{- end }}

{{/*
Frontend service/deployment name.
*/}}
{{- define "spliteasy.frontendName" -}}
{{- printf "%s-frontend" (include "spliteasy.fullname" .) }}
{{- end }}

{{/*
Common labels applied to every resource.
*/}}
{{- define "spliteasy.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend selector labels.
*/}}
{{- define "spliteasy.backendSelectorLabels" -}}
app.kubernetes.io/name: {{ include "spliteasy.name" . }}
app.kubernetes.io/component: backend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Frontend selector labels.
*/}}
{{- define "spliteasy.frontendSelectorLabels" -}}
app.kubernetes.io/name: {{ include "spliteasy.name" . }}
app.kubernetes.io/component: frontend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Full image reference — prepends registry if set.
Usage: {{ include "spliteasy.image" (dict "registry" .Values.imageRegistry "repo" .Values.backend.image.repository "tag" .Values.backend.image.tag) }}
*/}}
{{- define "spliteasy.image" -}}
{{- if .registry -}}
{{- printf "%s/%s:%s" .registry .repo .tag }}
{{- else -}}
{{- printf "%s:%s" .repo .tag }}
{{- end }}
{{- end }}
