from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor

from config import (
    BQ_LOCATION,
    DEFAULT_ARGS,
    # DESTINATION_DATASET,
    GCS_BUCKET,
    GCP_PROJECT,
    TABLES,
)

# TODO: Remove next definition and bring back the import from config
DESTINATION_DATASET = "raw_thelook_landing"

with DAG(
    dag_id="GCS_to_bigquery",
    description=("Extract GCS Parquet and load them into BigQuery"),
    start_date=datetime(2026, 11, 22),
    catchup=False,
    schedule="@daily",
    tags=["bigquery", "gcs", "parquet", "raw"],
    default_args=DEFAULT_ARGS,
) as dag:
    wait_for_extraction_task = ExternalTaskSensor(
        task_id="wait_for_extraction",
        external_dag_id="extract_to_GCS",
        external_task_id="extract_to_GCS_completed",
        allowed_states=["success"],
        failed_states=["failed"],
        check_existence=True,
        timeout=600,
        poke_interval=15,
        mode="reschedule",
    )

    create_raw_dataset_task = BigQueryCreateEmptyDatasetOperator(
        task_id="create_raw_dataset",
        project_id=GCP_PROJECT,
        dataset_id=DESTINATION_DATASET,
        location=BQ_LOCATION,
        exists_ok=True,
        gcp_conn_id="google_cloud_default",
    )

    load_tasks = []
    for table in TABLES:
        load_tasks.append(
            GCSToBigQueryOperator(
                task_id=f"load_{table}_to_bigquery",
                bucket=GCS_BUCKET,
                source_objects=[(f"raw/{table}/run_date={{{{ ds }}}}/part-*.parquet")],
                destination_project_dataset_table=(
                    f"{GCP_PROJECT}.{DESTINATION_DATASET}.{table}"
                ),
                source_format="PARQUET",
                autodetect=True,
                create_disposition="CREATE_IF_NEEDED",
                write_disposition="WRITE_TRUNCATE",  # APPEND + current True / False
                project_id=GCP_PROJECT,
                location=BQ_LOCATION,
                gcp_conn_id="google_cloud_default",
            )
        )

    wait_for_extraction_task >> create_raw_dataset_task >> load_tasks
