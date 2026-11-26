data "google_project" "this" {
  project_id = var.project_id
}

# Service account permissions to run Composer 3
resource "google_service_account_iam_member" "composer_agent" {
  service_account_id = google_service_account.sa["orchestrator"].name
  role               = "roles/composer.ServiceAgentV2Ext"
  member             = "serviceAccount:service-${data.google_project.this.number}@cloudcomposer-accounts.iam.gserviceaccount.com"

  depends_on = [google_project_service.enabled]
}

# Defining Composer 3 environment
resource "google_composer_environment" "airflow" {
  name   = "thelook-airflow"
  region = var.region

  config {
    environment_size = "ENVIRONMENT_SIZE_SMALL"
    
    software_config {
      image_version = var.composer_image_version

      pypi_packages = {
        polars = "==2.1.0"
      }

      env_variables = {
        DBT_REGION  = var.region
        DBT_JOB     = google_cloud_run_v2_job.dbt.name
        BQ_LOCATION         = var.bq_location
        RAW_DATASET         = local.raw_dataset
        DBT_DATASET         = local.dbt_dataset
        SOURCE_PROJECT      = "bigquery-public-data"
        SOURCE_DATASET      = "thelook_ecommerce"
        SOURCE_LOCATION     = "US"
      }
    }

    node_config {
      service_account = google_service_account.sa["orchestrator"].email
    }
  }

  depends_on = [
    google_project_iam_member.orchestrator_worker,
    google_service_account_iam_member.composer_agent,
  ]
}

# Convinient method to obtain bucket path for DAGs
output "composer_dags_prefix" {
  value = google_composer_environment.airflow.config[0].dag_gcs_prefix
}
