# =============================================================
# SRE RAG Agent — Terraform Main
# =============================================================

# --- Namespace ---
resource "kubernetes_namespace" "sre_rag" {
  metadata {
    name = var.namespace
    labels = {
      environment = var.environment
      managed-by  = "terraform"
      team        = "sre"
    }
  }
}

# --- Application Helm Release ---
resource "helm_release" "sre_rag" {
  name       = "sre-rag"
  chart      = "${path.module}/../helm/sre-rag"
  namespace  = kubernetes_namespace.sre_rag.metadata[0].name
  depends_on = [kubernetes_namespace.sre_rag]

  values = [
    file("${path.module}/../helm/sre-rag/values.yaml"),
    var.environment == "production" ? file("${path.module}/../helm/sre-rag/values-prod.yaml") : "",
  ]

  set {
    name  = "api.image.tag"
    value = var.api_image_tag
  }

  set {
    name  = "global.environment"
    value = var.environment
  }

  wait    = true
  timeout = 300
}

# --- Monitoring Stack (kube-prometheus-stack) ---
resource "helm_release" "monitoring" {
  count = var.monitoring_enabled ? 1 : 0

  name             = "monitoring"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "62.3.0"
  namespace        = "monitoring"
  create_namespace = true

  values = [
    <<-EOT
    prometheus:
      prometheusSpec:
        serviceMonitorSelectorNilUsesHelmValues: false
        serviceMonitorSelector: {}
        serviceMonitorNamespaceSelector: {}
        additionalScrapeConfigs:
          - job_name: 'sre-rag-api'
            kubernetes_sd_configs:
              - role: pod
                namespaces:
                  names:
                    - ${var.namespace}
            relabel_configs:
              - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
                action: keep
                regex: true
              - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
                action: replace
                target_label: __metrics_path__
              - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port, __meta_kubernetes_pod_ip]
                action: replace
                regex: (\d+);(([\da-fA-F.:]+))
                replacement: $2:$1
                target_label: __address__
        ruleSelector: {}
        ruleNamespaceSelector: {}

    grafana:
      adminPassword: admin
      dashboardProviders:
        dashboardproviders.yaml:
          apiVersion: 1
          providers:
            - name: 'sre-dashboards'
              orgId: 1
              folder: 'SRE'
              type: file
              disableDeletion: false
              editable: true
              options:
                path: /var/lib/grafana/dashboards/sre

    alertmanager:
      alertmanagerSpec:
        replicas: 1
      config:
        global:
          resolve_timeout: 5m
        route:
          group_by: ['alertname', 'namespace']
          group_wait: 10s
          group_interval: 5m
          repeat_interval: 12h
          receiver: 'default'
          routes:
            - match:
                severity: critical
              receiver: 'critical'
              continue: true
            - match:
                severity: warning
              receiver: 'warning'
        receivers:
          - name: 'default'
            webhook_configs:
              - url: 'http://localhost:9093/webhook'
          - name: 'critical'
            webhook_configs:
              - url: 'http://localhost:9093/webhook'
          - name: 'warning'
            webhook_configs:
              - url: 'http://localhost:9093/webhook'
    EOT
  ]

  wait    = true
  timeout = 600
}
