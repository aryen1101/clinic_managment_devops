terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.95, < 6.0"
    }
  }

  # Remote state (recommended for teams). Create the bucket first, then uncomment:
  # backend "s3" {
  #   bucket       = "clinic-terraform-state-<your-unique-suffix>"
  #   key          = "clinic/eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.tags
  }
}
