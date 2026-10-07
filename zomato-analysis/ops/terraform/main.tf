# ==============================================================================
# Terraform Master: Multi-Cloud Multi-Failover Production Infrastructure
# Orchestrates: AWS EKS (Primary) + GCP GKE (DR Failover) + Global Route 53 DNS
# Tier: Principal Cloud & SRE Platform Architect Standard
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

# --- Cloud Provider Configurations ---
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Tier        = "MultiCloud-Primary"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# --- Module 1: AWS EKS (Primary Cloud Infrastructure) ---
module "aws_primary_cluster" {
  source = "./modules/aws_eks"

  project_name        = var.project_name
  environment         = var.environment
  aws_region          = var.aws_region
  vpc_cidr            = var.aws_vpc_cidr
  cluster_version     = var.eks_cluster_version
  node_instance_types = var.eks_node_instance_types
  min_nodes           = var.eks_min_nodes
  max_nodes           = var.eks_max_nodes
}

# --- Module 2: GCP GKE (Disaster Recovery Failover Infrastructure) ---
module "gcp_failover_cluster" {
  source = "./modules/gcp_gke"

  project_name   = var.project_name
  environment    = var.environment
  gcp_project_id = var.gcp_project_id
  gcp_region     = var.gcp_region
  subnet_cidr    = var.gcp_subnet_cidr
  machine_type   = var.gke_machine_type
  min_nodes      = var.gke_min_nodes
  max_nodes      = var.gke_max_nodes
}

# --- Module 3: Global Traffic Management & Automated Multi-Cloud Failover ---
module "global_dns_failover" {
  source = "./modules/global_failover_dns"

  domain_name           = var.domain_name
  primary_endpoint_ip   = module.aws_primary_cluster.ingress_alb_ip
  secondary_endpoint_ip = module.gcp_failover_cluster.ingress_ip
}
