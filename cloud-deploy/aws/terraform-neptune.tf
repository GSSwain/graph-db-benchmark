# Terraform configuration for AWS Neptune Graph Database
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  default = "us-east-1"
}

provider "aws" {
  region = var.region
}

resource "aws_neptune_cluster" "finbench_neptune" {
  cluster_identifier                  = "finbench-neptune-cluster"
  engine                              = "neptune"
  backup_retention_period             = 1
  preferred_backup_window             = "07:00-09:00"
  skip_final_snapshot                 = true
  iam_database_authentication_enabled = false
  apply_immediately                   = true
}

resource "aws_neptune_cluster_instance" "finbench_instances" {
  count              = 2
  cluster_identifier = aws_neptune_cluster.finbench_neptune.id
  engine             = "neptune"
  instance_class     = "db.r5.2xlarge"
  apply_immediately  = true
}

resource "aws_s3_bucket" "finbench_bulk_data" {
  bucket_prefix = "finbench-bulk-loader-"
}

output "neptune_endpoint" {
  value = aws_neptune_cluster.finbench_neptune.endpoint
}
