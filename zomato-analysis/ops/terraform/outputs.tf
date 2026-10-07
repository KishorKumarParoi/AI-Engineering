# ==============================================================================
# Terraform Outputs: Multi-Cloud Multi-Region Production Topology
# ==============================================================================

output "aws_cluster_name" {
  description = "Name of the AWS Primary EKS cluster"
  value       = module.aws_primary_cluster.cluster_name
}

output "aws_cluster_endpoint" {
  description = "Kubernetes API endpoint for the AWS Primary EKS cluster"
  value       = module.aws_primary_cluster.cluster_endpoint
}

output "aws_ingress_ip" {
  description = "Active ingress IP of the AWS Primary cluster"
  value       = module.aws_primary_cluster.ingress_alb_ip
}

output "gcp_cluster_name" {
  description = "Name of the GCP Standby GKE cluster"
  value       = module.gcp_failover_cluster.cluster_name
}

output "gcp_cluster_endpoint" {
  description = "Kubernetes API endpoint for the GCP Standby GKE cluster"
  value       = module.gcp_failover_cluster.cluster_endpoint
}

output "gcp_ingress_ip" {
  description = "Passive ingress IP of the GCP Standby DR cluster"
  value       = module.gcp_failover_cluster.ingress_ip
}

output "global_failover_fqdn" {
  description = "Automated Failover Global Fully Qualified Domain Name"
  value       = module.global_dns_failover.fqdn
}

output "primary_health_check_id" {
  description = "AWS Route 53 Health Check ID for Primary Endpoint"
  value       = module.global_dns_failover.primary_health_check_id
}
