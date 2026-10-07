# ==============================================================================
# Global Traffic Routing & Automated Multi-Cloud DNS Failover Module
# Implements: Route 53 Active-Passive Multi-Cloud Failover (<30s RTO)
# AWS Primary (us-east-1) -> GCP Standby DR (us-central1)
# ==============================================================================

variable "domain_name" {
  type        = string
  description = "Top-level or sub-domain name for the service"
}

variable "primary_endpoint_ip" {
  type        = string
  description = "Public Load Balancer IP of the AWS Primary Cluster"
}

variable "secondary_endpoint_ip" {
  type        = string
  description = "Public Load Balancer IP of the GCP DR Cluster"
}

# --- Route 53 Public Hosted Zone ---
resource "aws_route53_zone" "primary_zone" {
  name = var.domain_name

  tags = {
    Environment = "production"
    Tier        = "global-dns"
  }
}

# --- Health Check: AWS Primary Endpoint ---
resource "aws_route53_health_check" "aws_primary" {
  ip_address        = var.primary_endpoint_ip
  port              = 80
  type              = "HTTP"
  resource_path     = "/health"
  request_interval  = 10
  failure_threshold = 3

  tags = {
    Name   = "primary-aws-eks-health-check"
    Region = "us-east-1"
  }
}

# --- Health Check: GCP DR Endpoint ---
resource "aws_route53_health_check" "gcp_secondary" {
  ip_address        = var.secondary_endpoint_ip
  port              = 80
  type              = "HTTP"
  resource_path     = "/health"
  request_interval  = 10
  failure_threshold = 3

  tags = {
    Name   = "secondary-gcp-gke-health-check"
    Region = "us-central1"
  }
}

# --- DNS Failover Record: AWS Primary Record (Active) ---
resource "aws_route53_record" "api_primary" {
  zone_id = aws_route53_zone.primary_zone.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  ttl     = 30

  failover_routing_policy {
    type = "PRIMARY"
  }

  set_identifier  = "primary-aws-us-east-1"
  records         = [var.primary_endpoint_ip]
  health_check_id = aws_route53_health_check.aws_primary.id
}

# --- DNS Failover Record: GCP DR Record (Passive / Standby) ---
resource "aws_route53_record" "api_secondary" {
  zone_id = aws_route53_zone.primary_zone.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  ttl     = 30

  failover_routing_policy {
    type = "SECONDARY"
  }

  set_identifier  = "secondary-gcp-us-central1"
  records         = [var.secondary_endpoint_ip]
  health_check_id = aws_route53_health_check.gcp_secondary.id
}

output "zone_id" {
  value = aws_route53_zone.primary_zone.zone_id
}

output "fqdn" {
  value = aws_route53_record.api_primary.fqdn
}

output "primary_health_check_id" {
  value = aws_route53_health_check.aws_primary.id
}

output "secondary_health_check_id" {
  value = aws_route53_health_check.gcp_secondary.id
}
