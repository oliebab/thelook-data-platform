#!/bin/bash
set -e

echo "Retrieving all DAG IDs..."

DAGS=(
    "extract_to_GCS"
    "historical_GCS_to_bigquery"
    "daily_GCS_to_bigquery"
)

for DAG in "${DAGS[@]}"; do
    (
        echo "Deleting DAG: $DAG"
        poetry run airflow dags delete "$DAG" --yes
        echo "Finished: $DAG"
    ) &
done

# Wait for all background processes
wait

echo "All DAG metadata deleted."
echo "Waiting for the DAG processor to rediscover DAGs..."
