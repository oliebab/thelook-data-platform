from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import (
    BigQueryToGCSOperator,
)
from airflow.providers.standard.operators.empty import EmptyOperator

from config import (
    DEFAULT_ARGS,
    GCP_PROJECT,
    GCS_BUCKET,
    SOURCE_DATASET,
    SOURCE_LOCATION,
    SOURCE_PROJECT,
    TABLES,
)

with DAG(
    dag_id="extract_to_GCS",
    description="Export of all TheLook tables from BigQuery to GCS as Parquet",
    start_date=datetime(2026, 11, 22),
    catchup=True,
    schedule="@Daily",
    tags=["bigquery", "gcs", "parquet"],
    default_args=DEFAULT_ARGS,
) as dag:
    extract_tasks = []
    for table in TABLES:
        extract_tasks.append(
            BigQueryToGCSOperator(
                task_id=f"extract_{table}_to_GCS",
                source_project_dataset_table=(
                    f"{SOURCE_PROJECT}.{SOURCE_DATASET}.{table}"
                ),
                destination_cloud_storage_uris=[
                    (
                        f"gs://{GCS_BUCKET}/raw/{table}/run_date={{{{ ds }}}}/part-*.parquet"
                    )
                ],
                export_format="PARQUET",
                compression="SNAPPY",
                project_id=GCP_PROJECT,
                gcp_conn_id="google_cloud_default",
                location=SOURCE_LOCATION,
            )
        )
