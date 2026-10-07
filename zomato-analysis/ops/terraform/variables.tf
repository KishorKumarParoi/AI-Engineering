# ==============================================================================
# Terraform Variables: Multi-Cloud Multi-Region Architecture
# Defines AWS EKS (Primary) and GCP GKE (Failover DR) configurations
# ==============================================================================

variable "environment" {
  description = "Target deployment environment (production, staging, dr)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Global project identifier"
  type        = string
  default     = "zomato-ai-platform"
}

# --- AWS Configuration (Primary Region) ---
variable "aws_region" {
  description = "Primary AWS region for active workloads"
  type        = string
  default     = "us-east-1"
}

variable "aws_vpc_cidr" {
  description = "VPC CIDR block for primary AWS network"
  type        = string
  default     = "10.100.0.0/16"
}

variable "eks_cluster_version" {
  description = "Kubernetes version for AWS EKS"
  type        = string
  default     = "1.30"
}

variable "eks_node_instance_types" {
  description = "EC2 instance types for EKS worker nodes"
  type        = list(string)
  default     = ["m6i.xlarge", "m5.xlarge"]
}

variable "eks_min_nodes" {
  description = "Minimum node count for primary EKS cluster"
  type        = number
  default     = 3
}

variable "eks_max_nodes" {
  description = "Maximum autoscaling node count for primary EKS cluster"
  type        = number
  default     = 10
}

# --- GCP Configuration (Disaster Recovery Failover Region) ---
variable "gcp_project_id" {
  description = "Google Cloud project ID for DR failover cluster"
  type        = string
  default     = "zomato-multicloud-dr"
}

variable "gcp_region" {
  description = "Secondary GCP region for active-passive DR failover"
  type        = string
  default     = "us-central1"
}

variable "gcp_subnet_cidr" {
  description = "Subnet CIDR for GCP DR VPC"
  type        = string
  default     = "10.200.0.0/16"
}

variable "gke_machine_type" {
  description = "GCE machine type for GKE failover node pool"
  type        = string
  default     = "e2-standard-4"
}

variable "gke_min_nodes" {
  description = "Minimum nodes in standby DR cluster"
  type        = number
  default     = 2
}

variable "gke_max_nodes" {
  description = "Maximum nodes in DR cluster during failover surge"
  type        = number
  default     = 12
}

# --- Global DNS & Failover ---
variable "domain_name" {
  description = "Public domain name for global API gateway"
  type        = string
  default     = "api.zomato-ai.com"
}
