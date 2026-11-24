
import json
import os
from datetime import date

from google.cloud import bigquery

# Default to an isolated test table.
PROJECT_ID = os.environ.get("GCP_PROJECT", "thelook-dp-2611")
DATASET = "reports"
TABLE = os.environ.get("REPORTS_TABLE", "llm_business_review_test")
TABLE_ID = f"{PROJECT_ID}.{DATASET}.{TABLE}"
LOCATION = os.environ.get("BQ_LOCATION", "US")

# Deliberately fake reporting period. Never use a real reporting week.
FAKE_PERIOD_START = date(2000, 1, 3)
FAKE_PERIOD_END = date(2000, 1, 9)

PERIOD_TYPE = "weekly"
MODEL = "fake-model"
PROMPT_VERSION = "fake-test-v1"


def main() -> None:
    """Insert a fake review into the configured test table."""

    # Require explicit opt-in if someone configures the production table.
    if TABLE == "llm_business_review":
        if os.environ.get("ALLOW_PRODUCTION_FAKE_WRITE") != "true":
            raise RuntimeError(
                "Refusing to write a fake review to the production table. "
                "Use REPORTS_TABLE=llm_business_review_test instead."
            )

    client = bigquery.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )

    table_id = TABLE_ID

    schema = [
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

    dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET}")
    dataset.location = LOCATION
    client.create_dataset(dataset, exists_ok=True)

    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)

    row = {
        "period_type": PERIOD_TYPE,
        "period_start": FAKE_PERIOD_START.isoformat(),
        "period_end": FAKE_PERIOD_END.isoformat(),
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "input_json": json.dumps(
            {
                "unit": "USD",
                "test": True,
                "description": "FAKE REVIEW - NOT REAL BUSINESS DATA",
            }
        ),
        "output_md": (
            "# FAKE REVIEW\n\n"
            "This is synthetic test data. "
            "It must not be used for business reporting."
        ),
        "guardrail_passed": True,
        "generated_at": "2000-01-03T12:00:00+00:00",
    }

    job = client.load_table_from_json(
        [row],
        table_id,
        job_config=bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        ),
    )

    job.result()

    print(f"Fake review successfully inserted into {table_id}")
    print(
        f"Reporting period: "
        f"{FAKE_PERIOD_START} to {FAKE_PERIOD_END}"
    )


if __name__ == "__main__":
    main()
