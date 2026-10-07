# ==============================================================================
# GCP GKE Disaster Recovery / Failover Cluster Module
# Provisions: Custom VPC, Subnetwork, Secondary Pod/Service CIDRs, GKE Cluster,
#             Auto-scaling Node Pool, Workload Identity
# ==============================================================================

variable "project_name" { type = string }
variable "environment" { type = string }
variable "gcp_project_id" { type = string }
variable "gcp_region" { type = string }
variable "subnet_cidr" { type = string }
variable "machine_type" { type = string }
variable "min_nodes" { type = number }
variable "max_nodes" { type = number }

# --- Custom VPC & Subnet ---
resource "google_compute_network" "dr_vpc" {
  name                    = "${var.project_name}-gcp-dr-vpc"
  auto_create_subnetworks = false
  project                 = var.gcp_project_id
}

resource "google_compute_subnetwork" "dr_subnet" {
  name          = "${var.project_name}-gcp-dr-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.gcp_region
  network       = google_compute_network.dr_vpc.id
  project       = var.gcp_project_id

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.48.0.0/14"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.52.0.0/20"
  }
}

# --- GKE Cluster (Control Plane) ---
resource "google_container_cluster" "dr_cluster" {
  name     = "${var.project_name}-gke-failover"
  location = var.gcp_region
  project  = var.gcp_project_id

  network    = google_compute_network.dr_vpc.name
  subnetwork = google_compute_subnetwork.dr_subnet.name

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
  }

  deletion_protection = false
}

# --- GKE Dedicated Worker Node Pool ---
resource "google_container_node_pool" "dr_nodes" {
  name     = "${var.project_name}-dr-node-pool"
  location = var.gcp_region
  cluster  = google_container_cluster.dr_cluster.name
  project  = var.gcp_project_id

  initial_node_count = var.min_nodes

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 50
    disk_type    = "pd-standard"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      role        = "dr-failover"
      environment = var.environment
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

output "cluster_name" {
  value = google_container_cluster.dr_cluster.name
}

output "cluster_endpoint" {
  value = google_container_cluster.dr_cluster.endpoint
}

output "cluster_ca_certificate" {
  value     = google_container_cluster.dr_cluster.master_auth[0].cluster_ca_certificate
  sensitive = true
}

output "ingress_ip" {
  value = "34.102.215.19" # Representative secondary DR Ingress IP
}
