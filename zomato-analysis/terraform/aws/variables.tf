variable "aws_region" {
  description = "Target AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment Environment (prod/staging/dev)"
  type        = string
  default     = "prod"
}
