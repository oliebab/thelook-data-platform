from airflow.sdk import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from docker.types import Mount

from config import CUTOFF_DATE, GCP_KEY_PATH

KEY = Mount(
    source=GCP_KEY_PATH,
    target="/app/keys/gcp-service-account.json",
    type="bind",
    read_only=True,
)


def dbt(task_id, command):
    return DockerOperator(
        task_id=task_id,
        image="thelook-dbt:latest",
        command=command,
        docker_url="unix://var/run/docker.sock",
        mounts=[KEY],
        mount_tmp_dir=False,
        auto_remove="success",
    )


with DAG("run_dbt", schedule="@daily", start_date=CUTOFF_DATE, catchup=False):
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

    freshness = dbt("dbt_source_freshness", "source freshness --target prod")
    build = dbt("dbt_build", "build --target prod")

    wait_for_load_task >> freshness >> build
