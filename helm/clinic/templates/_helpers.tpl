{{/* Resource names: <release>-backend, <release>-frontend, <release>-postgres ... */}}
{{- define "clinic.backend" -}}{{ .Release.Name }}-backend{{- end }}
{{- define "clinic.frontend" -}}{{ .Release.Name }}-frontend{{- end }}
{{- define "clinic.postgres" -}}{{ .Release.Name }}-postgres{{- end }}
{{- define "clinic.config" -}}{{ .Release.Name }}-config{{- end }}

{{- define "clinic.dbSecret" -}}
{{- if .Values.postgres.existingSecret -}}{{ .Values.postgres.existingSecret }}{{- else -}}{{ .Release.Name }}-db-secret{{- end -}}
{{- end }}

{{/* Labels shared by every resource */}}
{{- define "clinic.labels" -}}
app.kubernetes.io/part-of: clinic-management
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/* image reference, failing loudly if no tag was given */}}
{{- define "clinic.image" -}}
{{- $tag := required (printf "%s.tag is required (use a commit SHA)" .name) .cfg.tag -}}
{{ .cfg.image }}:{{ $tag }}
{{- end }}
