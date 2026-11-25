FROM python:3.12-slim as dbt

FROM python:3.12.8-slim as dbt

ENV PYTHONUNBUFFERED=1 \
    DBT_PROFILES_DIR=/app/dbt \
    DBT_TARGET_PATH=/tmp/dbt-target \
    DBT_LOG_PATH=/tmp/dbt-logs \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app/dbt

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first: this layer is only rebuilt when pyproject/lock change
COPY pyproject.toml poetry.lock ./
RUN pip3 install --upgrade --no-cache-dir pip \
    && pip3 install --no-cache-dir poetry \
    && poetry install --only main --no-root

# Then the dbt project itself
COPY . .

# `docker compose run --rm dbt build -s staging` == `dbt build -s staging`
ENTRYPOINT ["dbt"]
CMD ["--help"]
