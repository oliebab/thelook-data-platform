from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from airflow.providers.standard.operators.python import PythonOperator

from config import (
    BQ_LOCATION,
    CUTOFF_DATE,
    DEFAULT_ARGS,
    DESTINATION_DATASET,
    GCS_BUCKET,
    GCP_PROJECT,
    TABLES,
)

from load import enrich_parquet_files

with DAG(
    dag_id="daily_GCS_to_bigquery",
    description=("Extract GCS Parquet and load daily data into BigQuery"),
    start_date=CUTOFF_DATE + timedelta(days=1),
    catchup=True,
    schedule="@daily",
    tags=["bigquery", "gcs", "parquet", "raw", "enrich", "daily"],
    default_args=DEFAULT_ARGS,
) as dag:
    wait_for_extraction_task = ExternalTaskSensor(
        task_id="wait_for_extraction",
        external_dag_id="extract_to_GCS",
        external_task_id="extract_to_GCS_completed",
        allowed_states=["success"],
        failed_states=["failed"],
        check_existence=True,
        timeout=6000,
        poke_interval=15,
        mode="reschedule",
    )

    load_tasks = []
    enrich_tasks = []
    for table in TABLES:
        enrich_task = PythonOperator(
            task_id=f"enrich_{table}",
            python_callable=enrich_parquet_files,
            op_kwargs={
                "bucket": GCS_BUCKET,
                "table": table,
                "min_date": "{{ macros.ds_add(ds, -1) }}",
                "max_date": "{{ ds }}",
                "gcp_conn_id": "google_cloud_default",
            },
        )

        load_task = GCSToBigQueryOperator(
            task_id=f"load_{table}_to_bigquery",
            bucket=GCS_BUCKET,
            source_objects=[(f"staging/{table}/run_date={{{{ ds }}}}/part-*.parquet")],
            destination_project_dataset_table=(
                f"{GCP_PROJECT}.{DESTINATION_DATASET}.{table}"
            ),
            source_format="PARQUET",
            autodetect=True,
            create_disposition="CREATE_NEVER",
            write_disposition="WRITE_APPEND",
            project_id=GCP_PROJECT,
            location=BQ_LOCATION,
            gcp_conn_id="google_cloud_default",
        )

        enrich_tasks.append(enrich_task)
        load_tasks.append(load_task)

        wait_for_extraction_task >> enrich_task >> load_task
