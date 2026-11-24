"""Read one week from the KPI marts and return the JSON described in contracts/kpi_weekly.md.

All changes and highlight flags are computed here, so the model never does arithmetic.
Run on its own to print the JSON: poetry run python -m reporting.fetch_kpis --week-start 2026-11-16
"""

import argparse
import json
import os
import re
from datetime import date

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

# Contract order = review order. Unit "%" means a rate: changes in points, not percent.
KPIS = [
    ("gross_revenue", "USD"),
    ("net_revenue", "USD"),
    ("orders", "count"),
    ("average_order_value", "USD"),
    ("items_per_order", "count"),
    ("gross_margin_pct", "%"),
    ("cancellation_rate", "%"),
    ("return_rate", "%"),
    ("signups", "count"),
    ("new_buyers", "count"),
    ("repeat_order_share", "%"),
    ("sessions", "count"),
    ("session_conversion_rate", "%"),
    ("cart_abandonment_rate", "%"),
    ("product_to_cart_rate", "%"),
    ("cart_to_purchase_rate", "%"),
]

HIGHLIGHT_PCT = 5.0  # amounts and counts: |week-on-week change| >= 5%
HIGHLIGHT_PTS = 1.0  # rates: |week-on-week change| >= 1 point
TOP_CATEGORIES = 5

NOTES = [
    "Return rate for recent weeks is understated: returns are recorded weeks after purchase.",
    (
        "Source data is synthetic: session conversion is far above real e-commerce benchmarks; "
        "do not compare to industry averages."
    ),
]
LATEST_WEEK_NOTE = (
    "The most recent days of the source data are denser than earlier ones (synthetic generator), "
    "so large week-on-week increases in the latest week should be read with caution."
)


def pct_change(current: float | None, base: float | None) -> float | None:
    """Relative change in %, 1 decimal. None when either side is missing or the base is 0."""
    if current is None or base is None or base == 0:
        return None
    return round((current - base) / abs(base) * 100, 1)


def pts_change(current: float | None, base: float | None) -> float | None:
    """Difference in percentage points, 1 decimal."""
    if current is None or base is None:
        return None
    return round(current - base, 1)


def is_highlight(change: float | None, threshold: float) -> bool:
    return change is not None and abs(change) >= threshold


def kpi_entry(name: str, unit: str, row: dict) -> dict:
    current = row[f"{name}_current"]
    previous = row[f"{name}_previous"]
    year_ago = row[f"{name}_year_ago"]
    entry = {
        "unit": unit,
        "current": current,
        "previous": previous,
        "year_ago": year_ago,
    }

    if unit == "%":
        entry["wow_change_pts"] = pts_change(current, previous)
        entry["yoy_change_pts"] = pts_change(current, year_ago)
        entry["highlight"] = is_highlight(entry["wow_change_pts"], HIGHLIGHT_PTS)
    else:
        entry["wow_change_pct"] = pct_change(current, previous)
        entry["yoy_change_pct"] = pct_change(current, year_ago)
        entry["highlight"] = is_highlight(entry["wow_change_pct"], HIGHLIGHT_PCT)
    return entry


def channel_entry(row: dict) -> dict:
    wow = pct_change(row["sessions_current"], row["sessions_previous"])
    return {
        "traffic_source": row["traffic_source"],
        "sessions": row["sessions_current"],
        "sessions_wow_change_pct": wow,
        "session_conversion_rate": row["session_conversion_rate_current"],
        "highlight": is_highlight(wow, HIGHLIGHT_PCT),
    }


def category_entry(row: dict) -> dict:
    wow = pct_change(row["net_revenue_current"], row["net_revenue_previous"])
    return {
        "rank": row["net_revenue_rank"],
        "category": row["category"],
        "net_revenue": row["net_revenue_current"],
        "wow_change_pct": wow,
        "highlight": is_highlight(wow, HIGHLIGHT_PCT),
    }


def build_payload(
    kpi_row: dict,
    channel_rows: list[dict],
    category_rows: list[dict],
    is_latest_week: bool,
) -> dict:
    """Pure function (no BigQuery): mart rows in, contract JSON out. Tested in tests/test_fetch_kpis.py."""
    notes = list(NOTES)
    if is_latest_week:
        notes.append(LATEST_WEEK_NOTE)
    return {
        "period_type": "week",
        "period_start": kpi_row["week_start"].isoformat(),
        "period_end": kpi_row["week_end"].isoformat(),
        "currency": "USD",
        "kpis": {name: kpi_entry(name, unit, kpi_row) for name, unit in KPIS},
        "channels": [channel_entry(r) for r in channel_rows],
        "top_categories": [category_entry(r) for r in category_rows],
        "notes": notes,
    }


def _table(name: str) -> str:
    project = os.environ["GCP_PROJECT"]
    dataset = os.environ[
        "DBT_DATASET"
    ]  # dbt_<name> in development, analytics in production
    # Table names can't be query parameters, so check the dataset name before putting it in SQL.
    if not re.fullmatch(r"[A-Za-z0-9_]+", dataset):
        raise ValueError(f"Invalid DBT_DATASET: {dataset!r}")
    return f"`{project}.{dataset}.{name}`"


def _rows(client: bigquery.Client, sql: str, week_start: date) -> list[dict]:
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("week_start", "DATE", week_start)
        ]
    )
    return [dict(row) for row in client.query(sql, job_config=job_config).result()]


def latest_complete_week(client: bigquery.Client | None = None) -> date:
    client = client or bigquery.Client(project=os.environ["GCP_PROJECT"])
    sql = f"select max(week_start) as week_start from {_table('mart_kpi_weekly')}"
    week_start = next(iter(client.query(sql).result()))["week_start"]
    if week_start is None:
        raise ValueError("mart_kpi_weekly is empty")
    return week_start


def fetch_week(
    week_start: date | None = None, client: bigquery.Client | None = None
) -> dict:
    """Return the contract JSON for the ISO week starting on week_start (default: latest complete week)."""
    client = client or bigquery.Client(project=os.environ["GCP_PROJECT"])
    latest = latest_complete_week(client)
    week_start = week_start or latest
    if week_start.weekday() != 0:
        raise ValueError(f"{week_start} is not a Monday")

    kpi_rows = _rows(
        client,
        f"select * from {_table('mart_kpi_weekly')} where week_start = @week_start",
        week_start,
    )
    if not kpi_rows:
        raise ValueError(
            f"No complete week starting {week_start} in mart_kpi_weekly (latest is {latest})"
        )

    channel_rows = _rows(
        client,
        f"""select traffic_source, sessions_current, sessions_previous, session_conversion_rate_current
            from {_table("mart_channel_weekly")} where week_start = @week_start
            order by sessions_current desc""",
        week_start,
    )
    category_rows = _rows(
        client,
        f"""select net_revenue_rank, category, net_revenue_current, net_revenue_previous
            from {_table("mart_category_weekly")} where week_start = @week_start
              and net_revenue_rank <= {TOP_CATEGORIES}
            order by net_revenue_rank""",
        week_start,
    )
    return build_payload(
        kpi_rows[0], channel_rows, category_rows, is_latest_week=week_start == latest
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the KPI JSON for one week.")
    parser.add_argument(
        "--week-start", type=date.fromisoformat, help="Monday of the week, YYYY-MM-DD"
    )
    args = parser.parse_args()
    print(json.dumps(fetch_week(args.week_start), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
