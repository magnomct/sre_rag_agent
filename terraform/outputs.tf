# =============================================================
# SRE RAG Agent — Terraform Outputs
# =============================================================

output "namespace" {
  description = "Kubernetes namespace where the app is deployed"
  value       = kubernetes_namespace.sre_rag.metadata[0].name
}

output "environment" {
  description = "Current deployment environment"
  value       = var.environment
}

output "monitoring_enabled" {
  description = "Whether monitoring stack is deployed"
  value       = var.monitoring_enabled
}

output "api_image_tag" {
  description = "Deployed API image tag"
  value       = var.api_image_tag
}

output "port_forward_commands" {
  description = "Commands to port-forward services locally"
  value = {
    api          = "kubectl port-forward -n ${var.namespace} svc/sre-rag-api 8080:80"
    prometheus   = "kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090"
    grafana      = "kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
    alertmanager = "kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093"
  }
}
