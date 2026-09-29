# ──────────────────────────────────────────────────────────────
# Nexus-AI: Terraform GCP Module
# ──────────────────────────────────────────────────────────────
# Provisions: GCS Lakehouse Buckets, BigQuery Dataset,
#             GKE Cluster with GPU Node Pool, Artifact Registry
#
# Usage:
#   cd terraform/modules/gcp
#   terraform init
#   terraform plan -var="project_id=nexus-ai-prod"
#   terraform apply -auto-approve
# ──────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ── Variables ────────────────────────────────────────────────
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-south1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-south1-a"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "prod"
}

variable "enable_gpu" {
  description = "Enable GPU node pool for ML inference"
  type        = bool
  default     = false
}

# ── Provider ─────────────────────────────────────────────────
provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Local values ─────────────────────────────────────────────
locals {
  prefix = "nexus-ai-${var.environment}"
  labels = {
    project     = "nexus-ai"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# ══════════════════════════════════════════════════════════════
# 1. GCS Lakehouse Buckets (Bronze / Silver / Gold)
# ══════════════════════════════════════════════════════════════
resource "google_storage_bucket" "lakehouse" {
  for_each = toset(["bronze", "silver", "gold", "ml-artifacts"])

  name          = "${local.prefix}-lakehouse-${each.key}"
  location      = var.region
  storage_class = each.key == "bronze" ? "STANDARD" : "NEARLINE"
  force_destroy = var.environment != "prod"

  labels = local.labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = each.key == "bronze" ? 90 : 365
    }
    action {
      type = "Delete"
    }
  }

  uniform_bucket_level_access = true

  encryption {
    default_kms_key_name = ""  # Uses Google-managed encryption
  }
}

# ══════════════════════════════════════════════════════════════
# 2. BigQuery Dataset + Tables
# ══════════════════════════════════════════════════════════════
resource "google_bigquery_dataset" "lakehouse" {
  dataset_id                 = replace("${local.prefix}_lakehouse", "-", "_")
  friendly_name              = "Nexus-AI Lakehouse"
  description                = "Medallion architecture: Bronze → Silver → Gold"
  location                   = var.region
  default_table_expiration_ms = null
  delete_contents_on_destroy = var.environment != "prod"

  labels = local.labels

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }
  access {
    role          = "READER"
    special_group = "projectReaders"
  }
}

resource "google_bigquery_table" "gold_tables" {
  for_each = toset([
    "dim_restaurants", "dim_cuisines", "dim_delivery_partners",
    "fact_orders", "fact_daily_delivery_performance",
    "mart_city_revenue", "mart_hourly_demand",
    "features_delivery_eta_v1"
  ])

  dataset_id          = google_bigquery_dataset.lakehouse.dataset_id
  table_id            = each.key
  deletion_protection = var.environment == "prod"

  external_data_configuration {
    autodetect    = true
    source_format = "PARQUET"
    source_uris   = ["gs://${local.prefix}-lakehouse-gold/${each.key}/*.parquet"]
  }

  labels = local.labels
}

# ══════════════════════════════════════════════════════════════
# 3. GKE Cluster
# ══════════════════════════════════════════════════════════════
resource "google_container_cluster" "nexus" {
  name     = "${local.prefix}-gke"
  location = var.zone

  # Remove default node pool, use custom
  remove_default_node_pool = true
  initial_node_count       = 1

  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {}

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  resource_labels = local.labels
}

# ── Standard Node Pool (ETL + API) ──────────────────────────
resource "google_container_node_pool" "standard" {
  name       = "standard-pool"
  cluster    = google_container_cluster.nexus.name
  location   = var.zone
  node_count = 2

  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }

  node_config {
    machine_type = "e2-standard-4"
    disk_size_gb = 100

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = merge(local.labels, { pool = "standard" })

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# ── GPU Node Pool (ML Inference) ────────────────────────────
resource "google_container_node_pool" "gpu" {
  count = var.enable_gpu ? 1 : 0

  name       = "gpu-pool"
  cluster    = google_container_cluster.nexus.name
  location   = var.zone
  node_count = 0

  autoscaling {
    min_node_count = 0
    max_node_count = 2
  }

  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 200

    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = merge(local.labels, { pool = "gpu" })
    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }
}

# ══════════════════════════════════════════════════════════════
# 4. Artifact Registry
# ══════════════════════════════════════════════════════════════
resource "google_artifact_registry_repository" "nexus" {
  location      = var.region
  repository_id = "${local.prefix}-docker"
  format        = "DOCKER"
  description   = "Nexus-AI container images"
  labels        = local.labels
}

# ══════════════════════════════════════════════════════════════
# 5. Service Account
# ══════════════════════════════════════════════════════════════
resource "google_service_account" "nexus" {
  account_id   = "${local.prefix}-sa"
  display_name = "Nexus-AI Service Account"
}

resource "google_project_iam_member" "nexus_roles" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/container.developer",
    "roles/artifactregistry.writer",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.nexus.email}"
}

# ── Outputs ──────────────────────────────────────────────────
output "gke_cluster_name" {
  value = google_container_cluster.nexus.name
}

output "gke_endpoint" {
  value     = google_container_cluster.nexus.endpoint
  sensitive = true
}

output "lakehouse_buckets" {
  value = { for k, b in google_storage_bucket.lakehouse : k => b.url }
}

output "bigquery_dataset" {
  value = google_bigquery_dataset.lakehouse.dataset_id
}

output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.nexus.repository_id}"
}
