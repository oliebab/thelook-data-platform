from datetime import timedelta

from airflow import DAG
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from airflow.providers.standard.operators.python import PythonOperator

import pendulum

from config import (
    BQ_LOCATION,
    CUTOFF_DATE,
    DEFAULT_ARGS,
    DESTINATION_DATASET,
    GCS_BUCKET,
    GCP_PROJECT,
    TABLES,
    TABLES_JOIN,
)

from load import enrich_parquet_files

with DAG(
    dag_id="daily_GCS_to_bigquery",
    description=("Extract GCS Parquet and load daily data into BigQuery"),
    start_date=CUTOFF_DATE + timedelta(days=1),
    catchup=True,
    schedule="@daily",
    tags=["bigquery", "gcs", "parquet", "raw", "enrich", "historical"],
    default_args=DEFAULT_ARGS,
) as dag:
    for table in TABLES:
        wait_for_extraction_task = ExternalTaskSensor(
            task_id=f"wait_for_{table}_extraction",
            external_dag_id="extract_to_GCS",
            external_task_id=f"extract_{table}_to_GCS",
            allowed_states=["success"],
            failed_states=["failed"],
            check_existence=True,
            timeout=6000,
            poke_interval=15,
            mode="reschedule",
        )

        wait_for_historical_task = ExternalTaskSensor(
            task_id=f"wait_for_historical_{table}",
            external_dag_id="historical_GCS_to_bigquery",
            external_task_id=f"load_{table}_to_bigquery",
            execution_date_fn=lambda _: CUTOFF_DATE,
            allowed_states=["success"],
            failed_states=["failed"],
            mode="reschedule",
            poke_interval=60,
            timeout=6000,
        )

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
            write_disposition="WRITE_APPEND"
            if table not in TABLES_JOIN
            else "WRITE_TRUNCATE",
            project_id=GCP_PROJECT,
            location=BQ_LOCATION,
            gcp_conn_id="google_cloud_default",
        )

        wait_for_extraction_task >> wait_for_historical_task >> enrich_task >> load_task
