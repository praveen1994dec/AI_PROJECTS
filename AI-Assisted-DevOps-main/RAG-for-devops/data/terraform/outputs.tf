
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "Public Subnet IDs"
  value       = module.vpc.public_subnets
}

output "private_subnets" {
  description = "Private Subnet IDs"
  value       = module.vpc.private_subnets
}

output "cluster_name" {
  description = "EKS Cluster Name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API Server Endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "Kubernetes Version"
  value       = module.eks.cluster_version
}

output "cluster_arn" {
  description = "EKS Cluster ARN"
  value       = module.eks.cluster_arn
}


output "node_group_arns" {
  description = "Node Group ARNs"
  value       = module.eks.eks_managed_node_groups
}

output "frontend_repo_url" {
  description = "Frontend ECR Repo URL"
  value       = aws_ecr_repository.frontend.repository_url
}

output "backend_repo_url" {
  description = "Backend ECR Repo URL"
  value       = aws_ecr_repository.backend.repository_url
}
output "ec2_public_ip" {
  value = aws_instance.devops.public_ip
}
