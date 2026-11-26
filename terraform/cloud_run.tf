locals {
  registry = "${var.region}-docker.pkg.prod/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"

  common_env = {
    GCP_PROJECT = var.project_id
    RAW_DATASET = local.raw_dataset
    DBT_DATASET = local.dbt_dataset
    BQ_LOCATION = local.bq_location
  }
}

# Define DBT environment
resource "google_cloud_run_v2_job" "dbt" {
  name                = "thelook-dbt"
  location            = var.region
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.sa["dbt"].email
      max_retries     = 0
      timeout         = "1800s"

      containers {
        image   = "${local.registry}/dbt:${var.image_tag}"
        command = ["dbt"]

        dynamic "env" {
          for_each = local.common_env
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }

  depends_on = [google_project_service.enabled]
}

resource "google_cloud_run_v2_job_iam_member" "orchestrator_runs_dbt" {
  name     = google_cloud_run_v2_job.dbt.name
  location = google_cloud_run_v2_job.dbt.location
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.sa["orchestrator"].email}"
}

# Define Streamlit environment
resource "google_cloud_run_v2_service" "streamlit" {
  name                = "thelook-streamlit"
  location            = var.region
  invoker_iam_disabled = true
  deletion_protection = false

  template {
    service_account = google_service_account.sa["streamlit"].email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = "${local.registry}/streamlit:${var.image_tag}"

      ports { container_port = 8501 }

      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }

      dynamic "env" {
        for_each = local.common_env
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  depends_on = [google_project_service.enabled]
}
