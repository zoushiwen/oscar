{{- define "service.labels.standard" -}}
choerodon.io/release: {{ .Release.Name | quote }}
choerodon.io/infra: {{ .Chart.Name | quote }}
{{- end -}}