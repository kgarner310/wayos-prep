variable "project" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "alb_target_group_arn" { type = string }
variable "alb_security_group_id" { type = string }
variable "ecr_repository_url" { type = string }
variable "container_port" { type = number }
variable "cpu" { type = number }
variable "memory" { type = number }
variable "desired_count" { type = number }
variable "image_tag" { type = string }

variable "database_url_arn" { type = string }
variable "redis_url_arn" { type = string }
variable "jwt_secret_arn" { type = string }
variable "openai_api_key_arn" {
  type    = string
  default = ""
}
