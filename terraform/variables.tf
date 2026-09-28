# =============================================================
# SRE RAG Agent — Terraform Variables
# =============================================================

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubernetes context to use"
  type        = string
  default     = "kind-sre-rag"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "sre-rag"
}

variable "api_image_tag" {
  description = "Docker image tag for the API"
  type        = string
  default     = "latest"
}

variable "monitoring_enabled" {
  description = "Enable monitoring stack (Prometheus, Grafana, Alertmanager)"
  type        = bool
  default     = true
}
