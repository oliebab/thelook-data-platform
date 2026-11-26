#!/usr/bin/env bash

export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS="$AIRFLOW_USER:admin"
echo "{\"$AIRFLOW_USER\": \"$AIRFLOW_PASSWORD\"}" > "simple_auth_manager_passwords.json"

poetry run airflow api-server
