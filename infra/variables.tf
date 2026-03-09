variable "project" {
  type    = string
  default = "wayos-prep"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "ecs_cpu" {
  description = "Fargate CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "Fargate memory in MiB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  type    = number
  default = 1
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS. Set to empty string to use HTTP only."
  type        = string
  default     = ""
}

# Secrets Manager ARNs — create secrets manually, then pass ARNs here
variable "database_url_secret_arn" {
  description = "ARN of Secrets Manager secret containing DATABASE_URL"
  type        = string
}

variable "redis_url_secret_arn" {
  description = "ARN of Secrets Manager secret containing REDIS_URL"
  type        = string
}

variable "jwt_secret_arn" {
  description = "ARN of Secrets Manager secret containing JWT_SECRET_KEY"
  type        = string
}

variable "openai_api_key_secret_arn" {
  description = "ARN of Secrets Manager secret containing OPENAI_API_KEY"
  type        = string
  default     = ""
}
