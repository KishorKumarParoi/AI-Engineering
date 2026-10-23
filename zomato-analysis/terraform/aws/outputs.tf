output "vpc_id" {
  description = "The ID of the Zomato AI VPC"
  value       = aws_vpc.zomato_vpc.id
}

output "eks_cluster_name" {
  description = "EKS Cluster Name"
  value       = aws_eks_cluster.ai_eks_cluster.name
}

output "lakehouse_s3_bucket" {
  description = "Delta Lake S3 Bucket"
  value       = aws_s3_bucket.lakehouse_bucket.bucket
}

output "kms_key_arn" {
  description = "KMS Customer-Managed Key ARN"
  value       = aws_kms_key.lakehouse_kms_key.arn
}
