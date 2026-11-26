resource "google_artifact_registry_repository" "images" {
  repository_id = "thelook"
  location      = var.region
  format        = "DOCKER"
  description   = "Images for dbt and Streamlit"

  depends_on = [google_project_service.enabled]
}
