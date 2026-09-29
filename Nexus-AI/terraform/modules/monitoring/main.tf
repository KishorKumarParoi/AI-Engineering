# ──────────────────────────────────────────────────────────────
# Nexus-AI: Terraform Monitoring Module
# ──────────────────────────────────────────────────────────────
# Cloud-agnostic monitoring setup:
# - Prometheus Operator (via Helm)
# - Grafana (via Helm)
# - Alert routing to Slack/PagerDuty
# ──────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

variable "namespace" {
  type    = string
  default = "monitoring"
}

variable "grafana_admin_password" {
  type      = string
  sensitive = true
  default   = "nexus-ai-2024"
}

# ── Namespace ────────────────────────────────────────────────
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.namespace
    labels = {
      name        = var.namespace
      managed-by  = "terraform"
    }
  }
}

# ── Prometheus Stack ─────────────────────────────────────────
resource "helm_release" "prometheus" {
  name       = "prometheus"
  namespace  = var.namespace
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "58.0.0"

  set {
    name  = "prometheus.prometheusSpec.retention"
    value = "30d"
  }

  set {
    name  = "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage"
    value = "50Gi"
  }

  set {
    name  = "grafana.adminPassword"
    value = var.grafana_admin_password
  }

  set {
    name  = "grafana.service.type"
    value = "LoadBalancer"
  }

  # Scrape Nexus-AI namespace
  set {
    name  = "prometheus.prometheusSpec.serviceMonitorNamespaceSelector.matchLabels.monitoring"
    value = "enabled"
  }

  depends_on = [kubernetes_namespace.monitoring]
}

# ── ServiceMonitor for Nexus-AI ──────────────────────────────
resource "kubernetes_manifest" "nexus_service_monitor" {
  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    metadata = {
      name      = "nexus-inference-monitor"
      namespace = var.namespace
      labels = {
        app = "nexus-inference"
      }
    }
    spec = {
      namespaceSelector = {
        matchNames = ["nexus-ai"]
      }
      selector = {
        matchLabels = {
          app = "nexus-inference"
        }
      }
      endpoints = [{
        port     = "http"
        path     = "/metrics"
        interval = "15s"
      }]
    }
  }

  depends_on = [helm_release.prometheus]
}

output "prometheus_url" {
  value = "http://prometheus.${var.namespace}.svc.cluster.local:9090"
}

output "grafana_url" {
  value = "http://grafana.${var.namespace}.svc.cluster.local:3000"
}
