variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (staging, production-govcloud)"
  type        = string
  default     = "staging"
}

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "iot_rule_name" {
  description = "AWS IoT Core Rule Name"
  value       = aws_iot_topic_rule.telematics_stream.name
}
