# ──────────────────────────────────────────────────────────────
# Nexus-AI: Terraform Root Module — Multi-Cloud Orchestrator
# ──────────────────────────────────────────────────────────────
# Deploys the Nexus-AI platform across GCP, AWS, and Azure
# with configurable feature flags per cloud.
#
# Usage:
#   terraform init
#   terraform plan -var-file=environments/prod.tfvars
#   terraform apply -auto-approve
# ──────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "nexus-ai-terraform-state"
    prefix = "terraform/state"
  }
}

# ── Variables ────────────────────────────────────────────────
variable "environment" {
  type    = string
  default = "prod"
}

variable "enable_gcp" {
  type    = bool
  default = true
}

variable "enable_aws" {
  type    = bool
  default = false
}

variable "enable_azure" {
  type    = bool
  default = false
}

variable "gcp_project_id" {
  type    = string
  default = "nexus-ai-prod"
}

variable "enable_gpu" {
  type    = bool
  default = false
}

# ── GCP Module (Primary) ────────────────────────────────────
module "gcp" {
  count  = var.enable_gcp ? 1 : 0
  source = "./modules/gcp"

  project_id  = var.gcp_project_id
  region      = "asia-south1"
  environment = var.environment
  enable_gpu  = var.enable_gpu
}

# ── AWS Module (Secondary / Failover) ───────────────────────
module "aws" {
  count  = var.enable_aws ? 1 : 0
  source = "./modules/aws"

  region      = "ap-south-1"
  environment = var.environment
  enable_gpu  = var.enable_gpu
}

# ── Azure Module (Tertiary) ─────────────────────────────────
module "azure" {
  count  = var.enable_azure ? 1 : 0
  source = "./modules/azure"

  location    = "Central India"
  environment = var.environment
  enable_gpu  = var.enable_gpu
}

# ── Outputs ──────────────────────────────────────────────────
output "active_clouds" {
  value = compact([
    var.enable_gcp ? "GCP (Primary)" : "",
    var.enable_aws ? "AWS (Secondary)" : "",
    var.enable_azure ? "Azure (Tertiary)" : "",
  ])
}

output "gcp_outputs" {
  value     = var.enable_gcp ? module.gcp[0] : null
  sensitive = true
}

output "aws_outputs" {
  value     = var.enable_aws ? module.aws[0] : null
  sensitive = true
}

output "azure_outputs" {
  value     = var.enable_azure ? module.azure[0] : null
  sensitive = true
}
