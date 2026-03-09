variable "project" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "public_subnet_ids" { type = list(string) }
variable "container_port" { type = number }
variable "certificate_arn" { type = string }
variable "health_check_path" { type = string }
