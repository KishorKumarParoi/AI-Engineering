# ==============================================================================
# Terraform Enterprise Infrastructure as Code (AWS EKS, MSK Kafka, KMS, S3)
# Aligned with Phase 2 & Phase 4 of Enterprise AI Architect Roadmap
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. Dedicated Multi-AZ VPC
resource "aws_vpc" "zomato_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "zomato-ai-vpc"
    Project = "zomato-lakehouse"
    Tier    = "production"
  }
}

resource "aws_subnet" "private_az1" {
  vpc_id            = aws_vpc.zomato_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  tags              = { "kubernetes.io/role/internal-elb" = "1" }
}

resource "aws_subnet" "private_az2" {
  vpc_id            = aws_vpc.zomato_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"
  tags              = { "kubernetes.io/role/internal-elb" = "1" }
}

# 2. Customer-Managed KMS Key for Encryption at Rest
resource "aws_kms_key" "lakehouse_kms_key" {
  description             = "KMS Key for Zomato Delta Lake & MSK Kafka Encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "zomato-lakehouse-kms"
  }
}

# 3. Secure Delta Lake S3 Bucket
resource "aws_s3_bucket" "lakehouse_bucket" {
  bucket        = "zomato-delta-lakehouse-prod-${var.environment}"
  force_destroy = false
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lakehouse_encryption" {
  bucket = aws_s3_bucket.lakehouse_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.lakehouse_kms_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# 4. Amazon EKS Cluster for AI Serving & Streaming
resource "aws_eks_cluster" "ai_eks_cluster" {
  name     = "zomato-ai-eks-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids              = [aws_subnet.private_az1.id, aws_subnet.private_az2.id]
    endpoint_private_access = true
    endpoint_public_access  = true
  }
}

# 5. EKS IAM Cluster Role
resource "aws_iam_role" "eks_cluster_role" {
  name = "zomato-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}
