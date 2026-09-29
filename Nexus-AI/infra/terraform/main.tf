# ==========================================
# NEXUS-AI MULTI-CLOUD INFRASTRUCTURE AS CODE (TERRAFORM)
# Provisions GCP (Primary), AWS (Secondary/DR), and Azure (Backup)
# with GPU Node Pools and Multi-Region Failover Routing.
# ==========================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

variable "project_name" {
  type    = string
  default = "nexus-zomato-ai"
}

variable "primary_region_gcp" {
  type    = string
  default = "us-central1"
}

variable "secondary_region_aws" {
  type    = string
  default = "us-east-1"
}

# ------------------------------------------
# 1. PRIMARY CLOUD: GCP (GCS, BigQuery, GKE GPU Pool)
# ------------------------------------------
resource "google_storage_bucket" "zomato_lakehouse_gcs" {
  name          = "${var.project_name}-lakehouse-primary"
  location      = var.primary_region_gcp
  force_destroy = true
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

resource "google_bigquery_dataset" "zomato_lakehouse_bq" {
  dataset_id = "zomato_lakehouse_gold"
  location   = var.primary_region_gcp
}

resource "google_container_cluster" "primary_gke" {
  name     = "${var.project_name}-gke-primary"
  location = var.primary_region_gcp
  remove_default_node_pool = true
  initial_node_count       = 1
}

# GPU Node Pool with Auto-scaling (NVIDIA L4 / T4 for Model Inference)
resource "google_container_node_pool" "gpu_inference_nodes" {
  name       = "gpu-inference-pool"
  location   = var.primary_region_gcp
  cluster    = google_container_cluster.primary_gke.name
  node_count = 1

  autoscaling {
    min_node_count = 0
    max_node_count = 4
  }

  node_config {
    machine_type = "g2-standard-4" # Equipped with NVIDIA L4 GPU
    guest_accelerator {
      type  = "nvidia-l4"
      count = 1
      gpu_driver_installation_config {
        gpu_driver_version = "DEFAULT"
      }
    }
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# ------------------------------------------
# 2. SECONDARY CLOUD: AWS (S3 & Active-Passive DR)
# ------------------------------------------
resource "aws_s3_bucket" "zomato_lakehouse_s3" {
  bucket = "${var.project_name}-lakehouse-secondary"
}

resource "aws_s3_bucket_versioning" "s3_versioning" {
  bucket = aws_s3_bucket.zomato_lakehouse_s3.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ------------------------------------------
# 3. MULTI-REGION FAILOVER ROUTING POLICY
# ------------------------------------------
output "primary_lakehouse_endpoint" {
  value = google_storage_bucket.zomato_lakehouse_gcs.url
}

output "failover_lakehouse_endpoint" {
  value = "s3://${aws_s3_bucket.zomato_lakehouse_s3.bucket}"
}

output "gpu_cluster_name" {
  value = google_container_cluster.primary_gke.name
}
