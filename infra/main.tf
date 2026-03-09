terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # After first apply, uncomment and configure for remote state:
  # backend "s3" {
  #   bucket         = "wayos-prep-tfstate"
  #   key            = "infra/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "wayos-prep-tflock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "wayos-prep"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "vpc" {
  source = "./modules/vpc"

  project     = var.project
  environment = var.environment
  aws_region  = var.aws_region
}

module "ecr" {
  source = "./modules/ecr"

  project     = var.project
  environment = var.environment
}

module "alb" {
  source = "./modules/alb"

  project            = var.project
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  container_port     = var.container_port
  certificate_arn    = var.certificate_arn
  health_check_path  = "/health"
}

module "ecs" {
  source = "./modules/ecs"

  project             = var.project
  environment         = var.environment
  aws_region          = var.aws_region
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  alb_target_group_arn = module.alb.target_group_arn
  alb_security_group_id = module.alb.security_group_id
  ecr_repository_url  = module.ecr.repository_url
  container_port      = var.container_port
  cpu                 = var.ecs_cpu
  memory              = var.ecs_memory
  desired_count       = var.ecs_desired_count
  image_tag           = var.image_tag

  # Secrets (ARNs from AWS Secrets Manager — create these manually or via CLI)
  database_url_arn    = var.database_url_secret_arn
  redis_url_arn       = var.redis_url_secret_arn
  jwt_secret_arn      = var.jwt_secret_arn
  openai_api_key_arn  = var.openai_api_key_secret_arn
}
