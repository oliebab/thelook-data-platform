locals {
  service_accounts = {
    dbt          = "dbt, run as a Cloud Run Job"
    streamlit    = "Streamlit app on Cloud Run"
    orchestrator = "Cloud Composer environment"
  }
}

resource "google_service_account" "sa" {
  for_each     = local.service_accounts
  account_id   = "thelook-${each.key}"
  display_name = each.value

  depends_on = [google_project_service.enabled]
}

# Setup project level permissions
# DBT permissions
resource "google_project_iam_member" "dbt_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.sa["dbt"].email}"
}

# Streamlit permissions
resource "google_project_iam_member" "streamlit_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.sa["streamlit"].email}"
}

# Orchestrator permissions
resource "google_project_iam_member" "orchestrator_worker" {
  project = var.project_id
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.sa["orchestrator"].email}"
}

resource "google_project_iam_member" "orchestrator_run_viewer" {
  project = var.project_id
  role    = "roles/run.viewer"
  member  = "serviceAccount:${google_service_account.sa["orchestrator"].email}"
}

resource "google_service_account_iam_member" "orchestrator_acts_as_dbt" {
  service_account_id = google_service_account.sa["dbt"].name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.sa["orchestrator"].email}"
}

