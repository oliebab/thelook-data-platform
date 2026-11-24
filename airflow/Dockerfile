FROM python:3.12.8-slim AS airflow

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

ENV AIRFLOW_HOME=/app/airflow
ENV AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE=$AIRFLOW_HOME/simple_auth_manager_passwords.json

# Install curl
RUN apt-get update && apt-get install -y curl

WORKDIR $AIRFLOW_HOME

# Change to dedicated airflow pyproject
COPY pyproject.toml ./ 

RUN pip3 install --upgrade --no-cache-dir pip \
    && pip3 install poetry \
    && poetry install --only main

# Change location ?
COPY scripts scripts
RUN chmod +x scripts/entrypoint.sh
