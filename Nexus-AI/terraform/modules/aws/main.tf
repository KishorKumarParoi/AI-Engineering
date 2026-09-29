# ──────────────────────────────────────────────────────────────
# Nexus-AI: Terraform AWS Module
# ──────────────────────────────────────────────────────────────
# Provisions: S3 Lakehouse Buckets, Glue Catalog + Athena,
#             EKS Cluster with GPU Node Group, ECR
# ──────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "enable_gpu" {
  type    = bool
  default = false
}

provider "aws" {
  region = var.region
}

locals {
  prefix = "nexus-ai-${var.environment}"
  tags = {
    Project     = "nexus-ai"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ══════════════════════════════════════════════════════════════
# 1. S3 Lakehouse Buckets
# ══════════════════════════════════════════════════════════════
resource "aws_s3_bucket" "lakehouse" {
  for_each = toset(["bronze", "silver", "gold", "ml-artifacts"])
  bucket   = "${local.prefix}-lakehouse-${each.key}"
  tags     = local.tags
}

resource "aws_s3_bucket_versioning" "lakehouse" {
  for_each = aws_s3_bucket.lakehouse
  bucket   = each.value.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lakehouse" {
  for_each = aws_s3_bucket.lakehouse
  bucket   = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lakehouse" {
  for_each = aws_s3_bucket.lakehouse
  bucket   = each.value.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"
    transition {
      days          = each.key == "bronze" ? 30 : 90
      storage_class = "GLACIER"
    }
    expiration {
      days = each.key == "bronze" ? 180 : 730
    }
  }
}

# ══════════════════════════════════════════════════════════════
# 2. Glue Catalog + Athena
# ══════════════════════════════════════════════════════════════
resource "aws_glue_catalog_database" "lakehouse" {
  name        = replace("${local.prefix}_lakehouse", "-", "_")
  description = "Nexus-AI Medallion Lakehouse"
}

resource "aws_glue_crawler" "gold" {
  database_name = aws_glue_catalog_database.lakehouse.name
  name          = "${local.prefix}-gold-crawler"
  role          = aws_iam_role.glue.arn

  s3_target {
    path = "s3://${aws_s3_bucket.lakehouse["gold"].id}/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
  }

  tags = local.tags
}

resource "aws_athena_workgroup" "nexus" {
  name = "${local.prefix}-workgroup"
  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.lakehouse["ml-artifacts"].id}/athena-results/"
    }
    enforce_workgroup_configuration = true
  }
  tags = local.tags
}

# ══════════════════════════════════════════════════════════════
# 3. EKS Cluster
# ══════════════════════════════════════════════════════════════
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_eks_cluster" "nexus" {
  name     = "${local.prefix}-eks"
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids = data.aws_subnets.default.ids
  }

  tags = local.tags
}

resource "aws_eks_node_group" "standard" {
  cluster_name    = aws_eks_cluster.nexus.name
  node_group_name = "standard"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = data.aws_subnets.default.ids

  scaling_config {
    desired_size = 2
    max_size     = 5
    min_size     = 1
  }

  instance_types = ["m5.xlarge"]
  disk_size      = 100

  tags = merge(local.tags, { Pool = "standard" })
}

resource "aws_eks_node_group" "gpu" {
  count = var.enable_gpu ? 1 : 0

  cluster_name    = aws_eks_cluster.nexus.name
  node_group_name = "gpu"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = data.aws_subnets.default.ids

  scaling_config {
    desired_size = 0
    max_size     = 2
    min_size     = 0
  }

  instance_types = ["g4dn.xlarge"]
  disk_size      = 200

  taint {
    key    = "nvidia.com/gpu"
    value  = "present"
    effect = "NO_SCHEDULE"
  }

  tags = merge(local.tags, { Pool = "gpu" })
}

# ══════════════════════════════════════════════════════════════
# 4. ECR Repository
# ══════════════════════════════════════════════════════════════
resource "aws_ecr_repository" "nexus" {
  name                 = "${local.prefix}/nexus-ai"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.tags
}

# ══════════════════════════════════════════════════════════════
# 5. IAM Roles
# ══════════════════════════════════════════════════════════════
resource "aws_iam_role" "eks_cluster" {
  name = "${local.prefix}-eks-cluster-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "eks_cluster" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role" "eks_node" {
  name = "${local.prefix}-eks-node-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "eks_node_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
  ])
  role       = aws_iam_role.eks_node.name
  policy_arn = each.key
}

resource "aws_iam_role" "glue" {
  name = "${local.prefix}-glue-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "glue" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# ── Outputs ──────────────────────────────────────────────────
output "eks_cluster_name" {
  value = aws_eks_cluster.nexus.name
}

output "eks_endpoint" {
  value     = aws_eks_cluster.nexus.endpoint
  sensitive = true
}

output "s3_buckets" {
  value = { for k, b in aws_s3_bucket.lakehouse : k => b.arn }
}

output "ecr_repository" {
  value = aws_ecr_repository.nexus.repository_url
}

output "athena_workgroup" {
  value = aws_athena_workgroup.nexus.name
}
