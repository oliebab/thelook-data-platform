
import os
from datetime import date, datetime, timezone

from google.cloud import bigquery


PROJECT_ID = os.environ.get("GCP_PROJECT", "thelook-dp-2611")
DATASET = "reports"
TABLE = "llm_business_review"
TABLE_ID = f"{PROJECT_ID}.{DATASET}.{TABLE}"
LOCATION = os.environ.get("BQ_LOCATION", "US")


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
    """Create a BigQuery client."""
    return bigquery.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )


def ensure_table(
    client: bigquery.Client | None = None,
) -> None:
    """
    Create the dataset and table if missing.

    Safe to call on every run.
    New tables use daily partitioning and clustering.
    """
    client = client or _client()

    dataset = bigquery.Dataset(
        f"{PROJECT_ID}.{DATASET}"
    )
    dataset.location = LOCATION

    client.create_dataset(
        dataset,
        exists_ok=True,
    )

    table = bigquery.Table(
        TABLE_ID,
        schema=SCHEMA,
    )

    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="generated_at",
    )

    table.clustering_fields = [
        "period_type",
        "period_start",
        "prompt_version",
    ]

    client.create_table(
        table,
        exists_ok=True,
    )


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
    client: bigquery.Client | None = None,
) -> None:
    """
    Append one business review record to BigQuery.

    Historical runs are preserved, allowing comparisons
    between different models and prompt versions.

    Uses a BigQuery load job rather than streaming inserts.
    """
    client = client or _client()

    ensure_table(client)

    row = {
        "period_type": period_type,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "model": model,
        "prompt_version": prompt_version,

        # Pass the Python dictionary directly.
        # BigQuery handles JSON serialization.
        "input_json": input_json,

        "output_md": output_md,
        "guardrail_passed": guardrail_passed,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    job = client.load_table_from_json(
        [row],
        TABLE_ID,
        job_config=bigquery.LoadJobConfig(
            schema=SCHEMA,
            write_disposition=(
                bigquery.WriteDisposition.WRITE_APPEND
            ),
        ),
    )

    # Wait for completion and propagate errors.
    job.result()


def get_latest_reviews_query() -> str:
    """
    Return a query selecting the latest review
    for each reporting period.
    """
    return f"""
        SELECT *
        FROM `{TABLE_ID}`
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY period_type, period_start
            ORDER BY generated_at DESC
        ) = 1
    """


def get_review_history_query() -> str:
    """
    Return a query retrieving all historical runs.
    """
    return f"""
        SELECT *
        FROM `{TABLE_ID}`
        ORDER BY period_start DESC, generated_at DESC
    """


def get_prompt_comparison_query(
    period_start: date,
) -> str:
    """
    Return a query comparing prompt versions
    for a specific reporting period.
    """
    return f"""
        SELECT
            period_type,
            period_start,
            period_end,
            model,
            prompt_version,
            guardrail_passed,
            generated_at,
            JSON_VALUE(
                input_json,
                '$.kpis.net_revenue.current'
            ) AS net_revenue,
            output_md
        FROM `{TABLE_ID}`
        WHERE period_start = DATE '{period_start.isoformat()}'
        ORDER BY generated_at DESC
    """
