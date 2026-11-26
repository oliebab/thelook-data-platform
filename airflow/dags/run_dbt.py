import os
import shlex

from airflow.sdk import DAG
from airflow.providers.google.cloud.operators.cloud_run import (
    CloudRunExecuteJobOperator,
)
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor

from config import (
    CUTOFF_DATE,
    DEFAULT_ARGS,
    DEMO_END_DATE,
)


def dbt_task(task_id, command):
    args = shlex.split(command) if isinstance(command, str) else list(command)
    if args and args[0] == "dbt":
        args = args[1:]

    return CloudRunExecuteJobOperator(
        task_id=task_id,
        project_id=os.environ["GCP_PROJECT"],
        region=os.environ["DBT_REGION"],
        job_name=os.environ["DBT_JOB"],
        overrides={
            "container_overrides": [
                {
                    "args": args,
                }
            ]
        },
    )


with DAG(
    "run_dbt",
    schedule="@daily",
    start_date=CUTOFF_DATE,
    end_date=DEMO_END_DATE,
    catchup=False,
    tags=["bigquery", "dbt", "daily", "analytics"],
    default_args=DEFAULT_ARGS,
):
    wait_for_load_task = ExternalTaskSensor(
        task_id="wait_for_load",
        external_dag_id="daily_GCS_to_bigquery",
        allowed_states=["success"],
        failed_states=["failed"],
        check_existence=True,
        timeout=6000,
        poke_interval=15,
        mode="reschedule",
    )

    freshness = dbt_task("dbt_source_freshness", "source freshness --target prod")
    build = dbt_task("dbt_build", "build --target prod")

    wait_for_load_task >> freshness >> build
