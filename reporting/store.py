import json
import os
from datetime import date, datetime, timezone

from google.cloud import bigquery

PROJECT_ID = os.environ.get("GCP_PROJECT", "thelook-dp-2611")
DATASET = "reports"
TABLE = "llm_business_review"
TABLE_ID = f"{PROJECT_ID}.{DATASET}.{TABLE}"
LOCATION = os.environ.get("BQ_LOCATION", "US")  # must match your other datasets

SCHEMA = [
    bigquery.SchemaField("period_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("period_start", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("period_end", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("model", "STRING"),
    bigquery.SchemaField("prompt_version", "STRING"),
    bigquery.SchemaField("input_json", "JSON"),
    bigquery.SchemaField("output_md", "STRING"),
    bigquery.SchemaField("guardrail_passed", "BOOL"),
    bigquery.SchemaField("generated_at", "TIMESTAMP", mode="REQUIRED"),
]


def _client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID, location=LOCATION)


def ensure_table(client: bigquery.Client | None = None) -> None:
    """Create the dataset and table if missing. Safe to call on every run."""
    client = client or _client()
    ds = bigquery.Dataset(f"{PROJECT_ID}.{DATASET}")
    ds.location = LOCATION
    client.create_dataset(ds, exists_ok=True)
    client.create_table(bigquery.Table(TABLE_ID, schema=SCHEMA), exists_ok=True)


def store(
    *,
    period_type: str,
    period_start: date,
    period_end: date,
    model: str,
    prompt_version: str,
    input_json: dict,
    output_md: str,
    guardrail_passed: bool,
    replace: bool = True,
    client: bigquery.Client | None = None,
) -> None:
    """Write one row with a load job (not a streaming insert)."""
    client = client or _client()
    ensure_table(client)

    if replace:
        # A load job's rows can be deleted immediately, so a re-run for the
        # same period replaces the old row instead of duplicating it.
        client.query(
            f"DELETE FROM `{TABLE_ID}` "
            "WHERE period_type = @pt AND period_start = @ps",
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("pt", "STRING", period_type),
                    bigquery.ScalarQueryParameter("ps", "DATE", period_start),
                ]
            ),
        ).result()

    row = {
        "period_type": period_type,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "model": model,
        "prompt_version": prompt_version,
        "input_json": json.dumps(input_json, ensure_ascii=False),
        "output_md": output_md,
        "guardrail_passed": guardrail_passed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    job = client.load_table_from_json(
        [row],
        TABLE_ID,
        job_config=bigquery.LoadJobConfig(
            schema=SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        ),
    )
    job.result()  # raises if the load fails