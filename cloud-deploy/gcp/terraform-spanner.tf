# Terraform configuration for GCP Cloud Spanner Graph
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
}

provider "google" {
  project = var.project_id
  region  = "us-central1"
}

resource "google_spanner_instance" "finbench_spanner" {
  name         = "finbench-instance"
  config       = "regional-us-central1"
  display_name = "LDBC FinBench Spanner Graph Instance"
  num_nodes    = 3
}

resource "google_spanner_database" "finbench_db" {
  instance = google_spanner_instance.finbench_spanner.name
  name     = "finbench-db"
  version_retention_period = "3d"
}

output "spanner_instance_name" {
  value = google_spanner_instance.finbench_spanner.name
}
