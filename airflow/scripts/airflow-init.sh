#!/usr/bin/env bash
set -e

# Migrate database
poetry run airflow db migrate

# Create GCP connection
if ! poetry run airflow connections get google_cloud_default >/dev/null 2>&1; then
  poetry run airflow connections add google_cloud_default \
    --conn-type google_cloud_platform \
    --conn-extra "{ \"key_path\": \"/app/airflow/keys/gcp-service-account.json\", \"project\": \"$GCP_PROJECT\" }"
fi
