locals {
  raw_dataset = "raw_thelook"
  dbt_dataset = "analytics"
  llm_dataset = "reports"
  bq_location = "EU"
}

# Define datsets
resource "google_bigquery_dataset" "raw" {
  dataset_id = local.raw_dataset
  location   = var.bq_location

  lifecycle { prevent_destroy = true }
  depends_on = [google_project_service.enabled]
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id = local.dbt_dataset
  location   = var.bq_location

  lifecycle { prevent_destroy = true }
  depends_on = [google_project_service.enabled]
}

resource "google_bigquery_dataset" "reports" {
  dataset_id = local.llm_dataset
  location   = var.bq_location

  lifecycle { prevent_destroy = true }
  depends_on = [google_project_service.enabled]
}

# Define permissions for raw dataset: dbt reads / the orchestrator writes
resource "google_bigquery_dataset_iam_member" "raw_dbt_viewer" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.sa["dbt"].email}"
}

resource "google_bigquery_dataset_iam_member" "raw_orchestrator_editor" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.sa["orchestrator"].email}"
}

# Define permissions for DBT dataset: dbt and streamlit read
resource "google_bigquery_dataset_iam_member" "analytics_dbt_editor" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.sa["dbt"].email}"
}

resource "google_bigquery_dataset_iam_member" "analytics_streamlit_viewer" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.sa["streamlit"].email}"
}

# Define permissions for reports dataset: Streamlit reads
resource "google_bigquery_dataset_iam_member" "reports_streamlit_viewer" {
  dataset_id = google_bigquery_dataset.reports.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.sa["streamlit"].email}"
}

# The orchestrator runs BigQuery jobs for the raw loads
resource "google_project_iam_member" "orchestrator_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.sa["orchestrator"].email}"
}
