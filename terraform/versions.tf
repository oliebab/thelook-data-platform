terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "thelook-dp-2611-tfstate"
    prefix = "thelook/prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
